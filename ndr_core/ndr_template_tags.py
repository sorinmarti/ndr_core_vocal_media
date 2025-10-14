"""NDR Core template tags."""
import re
import json
import html
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from ndr_core.exceptions import PreRenderError
from ndr_core.forms.forms_manifest import ManifestSelectionForm
from ndr_core.models import NdrCoreUIElement, NdrCoreImage, NdrCoreUpload, NdrCorePage


class TextPreRenderer:
    """Class to pre-render text before it is displayed on the website."""

    MAX_ITERATIONS = 50
    ui_element_regex = r'\[\[(card|slideshow|carousel|jumbotron|figure|banner|iframe|manifest_viewer)\|(.*)\]\]'
    link_element_regex = r'\[\[(file|page|orcid)\|([0-9a-zA-Z_ -]*)\]\]'
    container_regex = r'\[\[(start|end)_(block)(?:=(.*?))?\]\]'
    code_start_regex = r'\[\[start_code(?:=(.*?))?\]\]'
    code_end_regex = r'\[\[end_code\]\]'
    toc_regex = r'\[\[toc\]\]'
    link_element_classes = {'figure': NdrCoreImage, 'file': NdrCoreUpload, 'page': NdrCorePage}
    link_element_keys = {"page": "view_name"}

    text = None
    block_titles = None

    def __init__(self, text, request):
        self.text = text
        self.request = request
        self.block_titles = []

    def check_tags_integrity(self):
        """Checks if all tags are well-formed. """
        matches = re.finditer(self.container_regex, self.text)
        items = {}
        for match in matches:
            block_type = match.groups(0)[1]
            if block_type not in items:
                items[block_type] = {'start': 0, 'end': 0}
            if match.groups(0)[0] == "start":
                items[block_type]['start'] += 1
            if match.groups(0)[0] == "end":
                items[block_type]['end'] += 1

        for key, value in items.items():
            if value['start'] != value['end']:
                return False
        return True

    def create_containers(self):
        """Creates container elements."""
        if self.check_tags_integrity():
            rendered_text = self.text
            match = re.search(self.container_regex, rendered_text)
            security_breaker = 0
            block_counter = 0

            while match:
                full_match = match.group(0)
                action = match.group(1)  # 'start' or 'end'
                block_type = match.group(2)  # 'block'
                title = match.group(3) if len(match.groups()) >= 3 else None  # optional title

                if action == 'start':
                    block_counter += 1
                    if title:
                        # Create slug from title for anchor ID
                        anchor_id = f"block-{block_counter}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}"
                        self.block_titles.append({'title': title, 'anchor': anchor_id})

                        replacement = (f'<div class="card mb-2 box-shadow" id="{anchor_id}">'
                                     f'<div class="card-body d-flex flex-column">'
                                     f'<h3 class="card-title">{title}</h3>')
                    else:
                        replacement = ('<div class="card mb-2 box-shadow">'
                                     '<div class="card-body d-flex flex-column">')
                elif action == 'end':
                    replacement = '</div></div>'

                rendered_text = rendered_text.replace(full_match, replacement, 1)
                match = re.search(self.container_regex, rendered_text)

                security_breaker += 1
                if security_breaker > 50:
                    raise PreRenderError("Too many container elements.")
        else:
            raise PreRenderError("Container tags are not well-formed.")
        return rendered_text

    def create_ui_elements(self):
        """Creates UI elements."""
        rendered_text = self.text
        match = re.search(self.ui_element_regex, rendered_text)
        security_breaker = 0
        while match:
            rendered_text = self.render_element(template=match.groups()[0],
                                                element_id=match.groups()[1],
                                                text=rendered_text)
            match = re.search(self.ui_element_regex, rendered_text)

            security_breaker += 1
            if security_breaker > self.MAX_ITERATIONS:
                raise PreRenderError("Too many UI element rendering iterations.")
        return rendered_text

    def create_links(self):
        """Creates links."""
        rendered_text = self.text
        match = re.search(self.link_element_regex, rendered_text)
        security_breaker = 0
        while match:
            template = match.groups()[0]
            rendered_text = self.render_element(template=template,
                                                element_id=match.groups()[1],
                                                text=rendered_text)

            match = re.search(self.link_element_regex, rendered_text)

            security_breaker += 1
            if security_breaker > self.MAX_ITERATIONS:
                raise PreRenderError("Too many link elements rendering iterations.")
        return rendered_text

    def create_toc(self):
        """Creates table of contents with anchor links to titled blocks."""
        rendered_text = self.text
        match = re.search(self.toc_regex, rendered_text)

        if match and self.block_titles:
            toc_html = '<div class="card mb-3 toc-container">'
            toc_html += '<div class="card-body">'
            toc_html += '<h4 class="card-title">Table of Contents</h4>'
            toc_html += '<ul class="list-unstyled">'

            for block in self.block_titles:
                toc_html += f'<li><a href="#{block["anchor"]}">{block["title"]}</a></li>'

            toc_html += '</ul>'
            toc_html += '</div>'
            toc_html += '</div>'

            rendered_text = rendered_text.replace('[[toc]]', toc_html)
        elif match and not self.block_titles:
            # If [[toc]] is present but no titled blocks exist, remove the tag
            rendered_text = rendered_text.replace('[[toc]]', '')

        return rendered_text

    def create_code_blocks(self):
        """Creates code blocks with optional syntax highlighting and pretty-printing."""
        rendered_text = self.text
        security_breaker = 0

        # Find start tag
        start_match = re.search(self.code_start_regex, rendered_text)

        while start_match:
            language = start_match.group(1) if start_match.group(1) else 'text'
            start_pos = start_match.end()

            # Find corresponding end tag
            end_match = re.search(self.code_end_regex, rendered_text[start_pos:])
            if not end_match:
                # No matching end tag found
                break

            end_pos = start_pos + end_match.start()

            # Extract content between tags
            code_content = rendered_text[start_pos:end_pos]

            # Strip HTML tags (like <p>, <br>, etc.) inserted by WYSIWYG editor
            # Remove all HTML tags but preserve the text content
            code_content = re.sub(r'<[^>]+>', '', code_content)

            # Unescape HTML entities that might be in the content
            code_content = html.unescape(code_content)

            # Strip leading/trailing whitespace but preserve internal formatting
            code_content = code_content.strip()

            # Pretty-print JSON if language is json
            if language.lower() == 'json':
                try:
                    parsed_json = json.loads(code_content)
                    code_content = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    # If JSON is invalid, just display as-is
                    pass

            # Escape HTML to prevent XSS
            code_content = html.escape(code_content)

            # Create the code block with language class for syntax highlighting
            code_html = f'<pre class="code-block"><code class="language-{language.lower()}">{code_content}</code></pre>'

            # Replace the entire block (from start tag to end tag) with the rendered HTML
            full_block = rendered_text[start_match.start():start_pos + end_match.end()]
            rendered_text = rendered_text.replace(full_block, code_html, 1)

            # Search for next code block
            start_match = re.search(self.code_start_regex, rendered_text)

            security_breaker += 1
            if security_breaker > self.MAX_ITERATIONS:
                raise PreRenderError("Too many code block rendering iterations.")

        return rendered_text

    def render_element(self, template, element_id,  text):
        """Renders an element."""
        if template == "orcid":
            # Validate ORCID format
            orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
            if not re.match(orcid_pattern, element_id):
                return text.replace(f"[[{template}|{element_id}]]",
                                    f"<span class='text-danger'>Invalid ORCID: {element_id}</span>")

            # Generate ORCID link
            orcid_url = f"https://orcid.org/{element_id}"
            orcid_html = f"""
            <a href="{orcid_url}" target="_blank" class="orcid-link" rel="noopener noreferrer">
                <img src="/static/ndr_core/images/orcid.svg" alt="ORCID" style="width: 16px; height: 16px; vertical-align: middle;">
                {element_id}
            </a>
            """
            return text.replace(f"[[{template}|{element_id}]]", orcid_html)

        element = self.get_element(template, element_id)
        context = {'data': element}

        if isinstance(element, NdrCoreUIElement) and element.type == NdrCoreUIElement.UIElementType.MANIFEST_VIEWER:
            group_id = element.items().first().manifest_group if element and element.items().exists() else None
            context['manifest_selection_form'] = ManifestSelectionForm(self.request.GET or None, manifest_group=group_id)

        element_html_string = render_to_string(f'ndr_core/ui_elements/{template}.html',
                                               request=self.request, context=context)
        text = text.replace(f'[[{template}|{element_id}]]', element_html_string)

        return text

    def get_element(self, template, element_id):
        """Returns an element."""
        if template in self.link_element_classes:
            element_class = self.link_element_classes[template]
        else:
            element_class = NdrCoreUIElement

        try:
            if template in self.link_element_keys:
                kw = {self.link_element_keys[template]: element_id}
            else:
                if element_id.isnumeric():
                    kw = {'pk': int(element_id)}
                else:
                    kw = {'pk': element_id}
            element = element_class.objects.get(**kw)
            return element
        except element_class.DoesNotExist:
            return None

    def get_pre_rendered_text(self):
        """Returns the pre-rendered text."""
        if self.text is None:
            raise PreRenderError("Text must not be None")
        if self.text == '':
            return self.text

        try:
            self.text = self.create_code_blocks()
            self.text = self.create_containers()
            self.text = self.create_toc()
            self.text = self.create_ui_elements()
            self.text = self.create_links()
        except PreRenderError as e:
            raise e
        return self.text
