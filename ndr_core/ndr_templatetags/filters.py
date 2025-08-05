import re
from datetime import datetime

from ndr_core.models import NdrCoreSearchField
from ndr_core.ndr_templatetags.abstract_filter import AbstractFilter
from ndr_core.ndr_templatetags.html_element import HTMLElement
from ndr_core.utils import get_nested_value


def get_get_filter_class(filter_name):
    """Returns the filter class."""
    if filter_name in ["lower", "upper", "title", "capitalize"]:
        return StringFilter
    if filter_name == "bool":
        return BoolFilter
    if filter_name == "fieldify":
        return FieldTemplateFilter
    if filter_name in ["badge", "pill"]:
        return BadgeTemplateFilter
    if filter_name == "img":
        return ImageTemplateFilter
    if filter_name == "date":
        return DateFilter
    if filter_name == "format":
        return NumberFilter
    if filter_name == "linkify":
        return LinkifyFilter
    if filter_name == "iframe":
        return IframeFilter


    raise ValueError(f"Filter {filter_name} not found.")


class StringFilter(AbstractFilter):
    """A class to represent a template filter."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return []

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the formatted string."""
        if self.filter_name == "upper":
            return self.get_value().upper()
        if self.filter_name == "lower":
            return self.get_value().lower()
        if self.filter_name == "title":
            return self.get_value().title()
        if self.filter_name == "capitalize":
            return self.get_value().capitalize()

        return self.get_value()


class BoolFilter(AbstractFilter):
    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return []

    def needed_options(self):
        return ["o0", "o1"]

    def get_rendered_value(self):
        true_value = "True"
        if self.get_configuration("o0"):
            true_value = self.get_configuration("o0")
        false_value = "False"
        if self.get_configuration("o1"):
            false_value = self.get_configuration("o1")

        if isinstance(self.value, bool):
            if self.value:
                return self.replace_key_values(true_value)
            return self.replace_key_values(false_value)

        if isinstance(self.value, str):
            if self.value.lower() == "true":
                return self.replace_key_values(true_value)
            return self.replace_key_values(false_value)

        return self.get_value()


class FieldTemplateFilter(AbstractFilter):
    """A class to represent a template filter."""

    field_value = ""
    search_field = None

    def __init__(self, filter_name, value, filter_configurations):
        super().__init__(filter_name, value, filter_configurations)
        try:
            self.search_field = NdrCoreSearchField.objects.get(
                field_name=self.get_configuration("o0")
            )
            try:
                self.field_value = self.search_field.get_list_choices_as_dict()[
                    self.value
                ][self.get_language_value_field_name()]
            except KeyError:
                self.field_value = self.value

        except NdrCoreSearchField.DoesNotExist:
            self.search_field = None

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return []

    def needed_options(self):
        return ["o0"]

    def get_rendered_value(self):
        """Returns the formatted string."""
        if not self.search_field:
            return self.get_value()

        return self.field_value


class BadgeTemplateFilter(AbstractFilter):
    """A class to represent a template filter."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["field", "color", "bg", "tt"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the formatted string."""

        badge_element = HTMLElement("span")
        badge_element.add_attribute("class", "badge")
        badge_element.add_attribute("class", "text-dark")
        badge_element.add_attribute("class", "font-weight-normal")

        if self.get_configuration("tt"):
            badge_element.add_attribute("data-toggle", "tooltip")
            badge_element.add_attribute("data-placement", "top")

        field_options = None
        if self.get_configuration("field"):
            # The 'field' option is set. Try to get a translated value from the NDRCoreSearchField
            try:
                field = NdrCoreSearchField.objects.get(
                    field_name=self.get_configuration("field")
                )
                all_field_options = field.get_choices_list_dict()
                field_options = all_field_options[self.value]
                if not field_options['is_printable']:
                    return None

                badge_element.add_content(
                    field_options[self.get_language_value_field_name()]
                )
                if self.get_configuration("tt"):
                    tt_content = self.get_configuration("tt")
                    if tt_content == "__field__":
                        tt_text = field_options[self.get_language_info_field_name()]
                    else:
                        tt_text = tt_content
                    badge_element.add_attribute("title", tt_text)
            except NdrCoreSearchField.DoesNotExist:
                badge_element.add_content("Field not found")  # TODO: internationalize
        else:
            badge_element.add_content(self.value)

        if self.get_configuration("color"):
            badge_element.manage_color_attribute(
                "color", self.get_configuration("color"), self.value, field_options
            )
        if self.get_configuration("bg"):
            badge_element.manage_color_attribute(
                "bg", self.get_configuration("bg"), self.value, field_options
            )

        return str(badge_element)


class ImageTemplateFilter(AbstractFilter):
    def __init__(self, filter_name, value, filter_configurations, data_context=None):
        super().__init__(filter_name, value, filter_configurations, data_context)

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["url", "iiif_resize", "width", "height", "alt", "class", "style", "title"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        # Determine the image URL
        if self.get_configuration("url"):
            # Use provided URL (with potential placeholders)
            url = self.get_configuration("url")
            if self.data_context:
                url = self.replace_placeholders(url)
        else:
            # Use the filter value as URL
            url = str(self.get_value())

        # Handle IIIF resize if specified
        if self.get_configuration("iiif_resize") and url:
            url = url.replace(
                "/full/0/default.",
                f'/pct:{self.get_configuration("iiif_resize")}/0/default.',
            )

        # Create the image element
        element = HTMLElement("img")
        element.add_attribute("src", url)

        # Set default attributes
        element.add_attribute("class", "img-fluid")
        element.add_attribute("alt", "Image")

        # Add optional attributes
        if self.get_configuration("width"):
            element.add_attribute("width", self.get_configuration("width"))

        if self.get_configuration("height"):
            element.add_attribute("height", self.get_configuration("height"))

        if self.get_configuration("alt"):
            element.add_attribute("alt", self.get_configuration("alt"))

        if self.get_configuration("class"):
            # Replace default class if custom class provided
            element.add_attribute("class", self.get_configuration("class"))

        if self.get_configuration("style"):
            element.add_attribute("style", self.get_configuration("style"))

        if self.get_configuration("title"):
            element.add_attribute("title", self.get_configuration("title"))

        return str(element)

    def replace_placeholders(self, url):
        """Replace [variable] placeholders in the URL with actual values."""
        import re
        from ndr_core.utils import get_nested_value

        # Find all [variable] patterns
        placeholders = re.findall(r'\[([^\]]+)\]', url)

        # Replace each placeholder with its value
        for placeholder in placeholders:
            try:
                # Get the value from the data context
                placeholder_value = get_nested_value(self.data_context, placeholder)
                if placeholder_value is not None:
                    # Handle arrays - take first element if it's a list
                    if isinstance(placeholder_value, list) and len(placeholder_value) > 0:
                        placeholder_value = placeholder_value[0]
                    url = url.replace(f'[{placeholder}]', str(placeholder_value))
                else:
                    url = url.replace(f'[{placeholder}]', '')
            except:
                # If placeholder can't be resolved, remove it
                url = url.replace(f'[{placeholder}]', '')

        return url


class DateFilter(AbstractFilter):
    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["format"]

    def needed_options(self):
        return ["o0"]

    def get_rendered_value(self):
        """Returns the formatted string."""
        common_formats = ["%Y-%m-%d"]
        if self.get_configuration("format"):
            common_formats = [self.get_configuration("format")]

        for d_format in common_formats:
            try:
                date_object = datetime.strptime(self.value, d_format)
                return date_object.strftime(self.get_configuration("o0"))
            except ValueError:
                pass

        return self.get_value()


class NumberFilter(AbstractFilter):
    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return []

    def needed_options(self):
        return ['o0']

    def get_rendered_value(self):
        """Returns the formatted string."""
        number_value = int(self.get_value())
        try:
            return ("{:" + self.get_configuration('o0') + "}").format(number_value)
        except ValueError:
            return self.get_value()

    def get_value(self):
        """Returns the formatted string."""
        return self.value


class LinkifyFilter(AbstractFilter):
    """A class to represent a linkify template filter that wraps content in an <a> tag."""

    def needed_attributes(self):
        return ["url"]  # URL is required

    def allowed_attributes(self):
        return ["url", "target", "class", "title", "rel"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the content wrapped in an <a> tag."""

        # Get the URL and replace placeholders
        url = self.get_configuration("url")
        if not url:
            return self.get_value()

        # Replace square bracket placeholders with actual values from data context
        url = self.replace_placeholders(url)

        # Create the link element
        link_element = HTMLElement("a")
        link_element.add_attribute("href", url)

        # Add optional attributes
        if self.get_configuration("target"):
            target = self.get_configuration("target")
            if target == "blank":
                target = "_blank"
            link_element.add_attribute("target", target)

        if self.get_configuration("class"):
            link_element.add_attribute("class", self.get_configuration("class"))

        if self.get_configuration("title"):
            link_element.add_attribute("title", self.get_configuration("title"))

        if self.get_configuration("rel"):
            link_element.add_attribute("rel", self.get_configuration("rel"))
        elif self.get_configuration("target") == "_blank":
            # Add security attribute for external links
            link_element.add_attribute("rel", "noopener noreferrer")

        # Add the content (which could be the result of previous filters)
        link_element.add_content(str(self.get_value()))

        return str(link_element)

    def replace_placeholders(self, url):
        """Replace [variable] placeholders in the URL with actual values."""

        # Find all [variable] patterns
        placeholders = re.findall(r'\[([^\]]+)\]', url)

        # Replace each placeholder with its value
        for placeholder in placeholders:
            try:
                # Get the value from the data context
                # This assumes self.data_context is available (you might need to pass this)
                placeholder_value = get_nested_value(self.data_context, placeholder)
                if placeholder_value is not None:
                    url = url.replace(f'[{placeholder}]', str(placeholder_value))
                else:
                    url = url.replace(f'[{placeholder}]', '')
            except:
                # If placeholder can't be resolved, leave it as is or remove it
                url = url.replace(f'[{placeholder}]', '')

        return url


class IframeFilter(AbstractFilter):
    """A class to represent an iframe template filter that embeds content in an <iframe> tag."""

    def __init__(self, filter_name, value, filter_configurations, data_context=None):
        super().__init__(filter_name, value, filter_configurations, data_context)

    def needed_attributes(self):
        return []  # No required attributes

    def allowed_attributes(self):
        return ["width", "height", "title", "frameborder", "allowfullscreen",
                "sandbox", "loading", "referrerpolicy", "class", "style", "src"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns an iframe element with the value as src or embedded content."""

        # Get the source URL - could be the filter value or from src parameter
        src_url = self.get_configuration("src") or self.get_value()

        # Replace placeholders in URL if data context is available
        if self.data_context and src_url:
            src_url = self.replace_placeholders(str(src_url))

        # Create the iframe element
        iframe_element = HTMLElement("iframe")
        iframe_element.add_attribute("src", src_url)

        # Set default attributes for security and usability
        iframe_element.add_attribute("frameborder", "0")
        iframe_element.add_attribute("loading", "lazy")

        # Add optional attributes with defaults
        width = self.get_configuration("width") or "100%"
        height = self.get_configuration("height") or "400"
        iframe_element.add_attribute("width", width)
        iframe_element.add_attribute("height", height)

        # Add title for accessibility
        title = self.get_configuration("title") or "Embedded content"
        iframe_element.add_attribute("title", title)

        # Handle security attributes
        if self.get_configuration("sandbox"):
            iframe_element.add_attribute("sandbox", self.get_configuration("sandbox"))

        if self.get_configuration("allowfullscreen"):
            if self.get_configuration("allowfullscreen").lower() in ["true", "1", "yes"]:
                iframe_element.add_attribute("allowfullscreen", "")

        # Handle loading attribute
        if self.get_configuration("loading"):
            iframe_element.add_attribute("loading", self.get_configuration("loading"))

        # Handle referrer policy
        if self.get_configuration("referrerpolicy"):
            iframe_element.add_attribute("referrerpolicy", self.get_configuration("referrerpolicy"))

        # Add CSS class if specified
        if self.get_configuration("class"):
            iframe_element.add_attribute("class", self.get_configuration("class"))

        # Add inline styles if specified
        if self.get_configuration("style"):
            iframe_element.add_attribute("style", self.get_configuration("style"))

        # Override frameborder if explicitly set
        if self.get_configuration("frameborder"):
            iframe_element.add_attribute("frameborder", self.get_configuration("frameborder"))

        return str(iframe_element)

    def replace_placeholders(self, url):
        """Replace [variable] placeholders in the URL with actual values."""
        import re
        from ndr_core.utils import get_nested_value

        # Find all [variable] patterns
        placeholders = re.findall(r'\[([^\]]+)\]', url)

        # Replace each placeholder with its value
        for placeholder in placeholders:
            try:
                # Get the value from the data context
                placeholder_value = get_nested_value(self.data_context, placeholder)
                if placeholder_value is not None:
                    url = url.replace(f'[{placeholder}]', str(placeholder_value))
                else:
                    url = url.replace(f'[{placeholder}]', '')
            except:
                # If placeholder can't be resolved, remove it
                url = url.replace(f'[{placeholder}]', '')

        return url
