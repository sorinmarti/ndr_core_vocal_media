import re
from datetime import datetime
import uuid
import json
from urllib.parse import urlparse

from ndr_core.models import NdrCoreSearchField, NdrCorePage
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
    if filter_name == "fieldinfo":
        return FieldInfoTemplateFilter
    if filter_name == "list":
        return ListTemplateFilter
    if filter_name in ["badge", "pill"]:
        return BadgeTemplateFilter
    if filter_name == "img":
        return ImageTemplateFilter
    if filter_name == "date":
        return DateFilter
    if filter_name == "format":
        return NumberFilter
    if filter_name == "readable":
        return ReadableNumberFilter
    if filter_name == "compact":
        return CompactNumberFilter
    if filter_name == "relative":
        return RelativeDateFilter
    if filter_name == "linkify":
        return LinkifyFilter
    if filter_name == "weblinks":
        return WeblinksFilter
    if filter_name == "orcid":
        return LinkifyFilter
    if filter_name == "iframe":
        return IframeFilter
    if filter_name == "default":
        return DefaultFilter
    if filter_name == "map":
        return MapFilter
    if filter_name in ["truncate", "text"]:
        return TextTruncateFilter

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

    def __init__(self, filter_name, value, filter_configurations, data_context=None):
        super().__init__(filter_name, value, filter_configurations, data_context)
        try:
            self.search_field = NdrCoreSearchField.objects.get(
                field_name=self.get_configuration("o0")
            )
            try:
                self.field_value = self.search_field.get_choices_list_dict()[
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


class FieldInfoTemplateFilter(AbstractFilter):
    """A class to represent a template filter that returns the info text of a field value."""

    field_info = ""
    search_field = None

    def __init__(self, filter_name, value, filter_configurations, data_context=None):
        super().__init__(filter_name, value, filter_configurations, data_context)
        try:
            self.search_field = NdrCoreSearchField.objects.get(
                field_name=self.get_configuration("o0")
            )
            try:
                self.field_info = self.search_field.get_choices_list_dict()[
                    self.value
                ][self.get_language_info_field_name()]
            except KeyError:
                self.field_info = ""

        except NdrCoreSearchField.DoesNotExist:
            self.search_field = None

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return []

    def needed_options(self):
        return ["o0"]

    def get_rendered_value(self):
        """Returns the info text."""
        if not self.search_field:
            return ""

        return self.field_info


class ListTemplateFilter(AbstractFilter):
    """A class to represent a template filter that renders lists as HTML ul or ol."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["type", "class"]

    def needed_options(self):
        return []

    def processes_list_as_whole(self):
        """This filter needs to process the entire list at once."""
        return True

    def get_rendered_value(self):
        """Returns the formatted string."""
        value = self.value

        if not isinstance(value, list):
            return self.get_value()

        if len(value) == 0:
            return ""

        list_type = self.get_configuration("type") or "ul"
        list_class = self.get_configuration("class") or ""

        class_attr = f' class="{list_class}"' if list_class else ""

        if list_type == "ol":
            html = f"<ol{class_attr}>"
        else:
            html = f"<ul{class_attr}>"

        for item in value:
            if isinstance(item, dict):
                item_str = str(item)
            else:
                item_str = str(item)
            html += f"<li>{item_str}</li>"

        if list_type == "ol":
            html += "</ol>"
        else:
            html += "</ul>"

        return html


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
            if not self.get_configuration("field"):
                # Replace placeholders in tooltip text
                tt_text = self.get_configuration("tt")
                if self.data_context:
                    tt_text = self.replace_placeholders(tt_text)
                badge_element.add_attribute("title", tt_text)

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
                        # Replace placeholders in tooltip text
                        tt_text = tt_content
                        if self.data_context:
                            tt_text = self.replace_placeholders(tt_text)
                    badge_element.add_attribute("title", tt_text)
            except NdrCoreSearchField.DoesNotExist:
                badge_element.add_content("Field not found")  # TODO: internationalize
        else:
            badge_element.add_content(self.get_value())

        if self.get_configuration("color"):
            badge_element.manage_color_attribute(
                "color", self.get_configuration("color"), self.get_value(), field_options
            )
        if self.get_configuration("bg"):
            badge_element.manage_color_attribute(
                "bg", self.get_configuration("bg"), self.get_value(), field_options
            )

        return str(badge_element)

    def replace_placeholders(self, text):
        """Replace [variable] placeholders in the text with actual values."""
        # Find all [variable] patterns
        placeholders = re.findall(r'\[([^\]]+)\]', text)

        # Replace each placeholder with its value
        for placeholder in placeholders:
            try:
                # Get the value from the data context
                placeholder_value = get_nested_value(self.data_context, placeholder)
                if placeholder_value is not None:
                    # Handle arrays - take first element if it's a list
                    if isinstance(placeholder_value, list) and len(placeholder_value) > 0:
                        placeholder_value = placeholder_value[0]
                    text = text.replace(f'[{placeholder}]', str(placeholder_value))
                else:
                    text = text.replace(f'[{placeholder}]', '')
            except:
                # If placeholder can't be resolved, remove it
                text = text.replace(f'[{placeholder}]', '')

        return text


class ImageTemplateFilter(AbstractFilter):

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["url", "iiif_resize", "iiif_full", "width", "height", "alt", "class", "style", "title"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        # Check the base value first - this determines if we should show default
        value = self.get_value()
        if value == self.get_default_value():
            # If the value is the default, return it
            return value

        # Determine the image URL
        if self.get_configuration("url"):
            # Use provided URL (with potential placeholders)
            url = self.get_configuration("url")
            if self.data_context:
                url = self.replace_placeholders(url)
        else:
            # Use the filter value as URL
            url = str(value)

        # Handle IIIF resize if specified
        if self.get_configuration("iiif_resize") and url:
            url = url.replace(
                "/full/0/default.",
                f'/pct:{self.get_configuration("iiif_resize")}/0/default.',
            )

        if self.get_configuration("iiif_full") and url:
            if self.get_configuration("iiif_full").lower() in ["true", "1", "yes"]:
                url = re.sub(r'/\d+,\d+,\d+,\d+/', '/full/', url)

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
        value = self.get_value()

        # Try to convert to number (int or float)
        try:
            # First try as float to preserve decimal values
            if isinstance(value, str):
                # Check if it contains a decimal point
                if '.' in value:
                    number_value = float(value)
                else:
                    number_value = int(value)
            elif isinstance(value, (int, float)):
                number_value = value
            else:
                return self.get_value()

            # Apply the format specification
            return ("{:" + self.get_configuration('o0') + "}").format(number_value)
        except (ValueError, TypeError):
            return self.get_value()

    def get_value(self):
        """Returns the formatted string."""
        return self.value


class LinkifyFilter(AbstractFilter):
    """A class to represent a linkify template filter that wraps content in an <a> tag."""

    def needed_attributes(self):
        return []  # No required attributes now - we have multiple ways to specify URL

    def allowed_attributes(self):
        return ["url", "page", "page_url", "params", "target", "class", "title", "rel"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the content wrapped in an <a> tag."""

        # Handle ORCID-specific case
        if self.filter_name == "orcid":
            orcid = self.get_value()
            orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
            if re.match(orcid_pattern, orcid):
                orcid_url = f"https://orcid.org/{orcid}"
                return f"""
                        <a href="{orcid_url}" target="_blank" class="orcid-link" rel="noopener noreferrer">
                            <img src="/static/ndr_core/images/orcid.svg" alt="ORCID" style="width: 16px; height: 16px; vertical-align: middle;">
                            {orcid}
                        </a>
                        """
            else:
                return f"<span class='text-danger'>Invalid ORCID: {orcid}</span>"

        # Determine the URL from various sources
        url = self.build_url()
        if not url:
            return self.get_value()

        # Add GET parameters if specified
        url = self.add_get_parameters(url)

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

    def build_url(self):
        """Build URL from various configuration options."""
        # Option 1: Direct URL with placeholders
        if self.get_configuration("url"):
            url = self.get_configuration("url")
            if self.data_context:
                url = self.replace_placeholders(url)
            return url

        # Option 2: Use page_url attribute - expects page object with url() method
        if self.get_configuration("page_url"):
            page_ref = self.get_configuration("page_url")
            if self.data_context:
                try:
                    # Get page object from data context
                    page_obj = get_nested_value(self.data_context, page_ref)
                    if page_obj and hasattr(page_obj, 'url'):
                        return page_obj.url()
                except:
                    pass

        # Option 3: Page view_name or ID lookup
        if self.get_configuration("page"):
            page_ref = self.get_configuration("page")

            # Replace placeholders in page reference
            if self.data_context:
                page_ref = self.replace_placeholders(page_ref)

            try:
                # Try to get page by view_name first
                try:
                    page = NdrCorePage.objects.get(view_name=page_ref)
                except NdrCorePage.DoesNotExist:
                    # Try by ID if it's numeric
                    if page_ref.isdigit():
                        page = NdrCorePage.objects.get(pk=int(page_ref))
                    else:
                        return None

                # Use the page's url() method
                return page.url()
            except (NdrCorePage.DoesNotExist, ValueError):
                return None

        return None

    def add_get_parameters(self, url):
        """Add GET parameters to URL if specified."""
        if not self.get_configuration("params"):
            return url

        params_config = self.get_configuration("params")

        # Replace placeholders in params if data context is available
        if self.data_context:
            params_config = self.replace_placeholders(params_config)

        # Parse parameters (format: "param1=value1,param2=value2")
        try:
            from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

            # Parse the current URL
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # Parse new parameters
            param_pairs = params_config.split(',')
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Add to query params (convert to list format expected by parse_qs)
                    query_params[key] = [value]

            # Rebuild URL with new query parameters
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed_url._replace(query=new_query)
            return urlunparse(new_parsed)
        except:
            # If parsing fails, just append parameters with ? or &
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}{params_config}"

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


class WeblinksFilter(AbstractFilter):
    """A filter to generate a list of favicons linking to the provided URLs."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["class", "style", "target"]

    def needed_options(self):
        return []

    def processes_list_as_whole(self):
        """This filter processes the entire list as a whole."""
        return True

    def get_rendered_value(self):
        """Generates a list of favicons linking to the provided URLs."""
        value = self.get_value()

        if not isinstance(value, list):
            return value

        if not value:
            return f"<span class='text-muted'>No URLs provided</span>"

        # Default attributes
        link_target = self.get_configuration("target") or "_blank"
        link_class = self.get_configuration("class") or "weblink"
        link_style = self.get_configuration("style") or ""
        default_icon = self.get_configuration("default_icon") or "/static/ndr_core/images/not-found-favicon.ico"

        # Generate HTML for each URL
        links_html = []
        for url in value:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            favicon_url = f"{base_url}/favicon.ico"
            link_html = f"""
                       <a href="{url}" target="{link_target}" class="{link_class}" style="{link_style}"
                          data-bs-toggle="tooltip" title="{url}">
                           <img src="{favicon_url}" alt="{parsed.netloc}" 
                                onerror="this.onerror=null;this.src='{default_icon}';" 
                                style="width: 16px; height: 16px; vertical-align: middle;">
                       </a>
                       """
            links_html.append(link_html)

        # Wrap in a container
        return f"<div>{''.join(links_html)}</div>"

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



class DefaultFilter(AbstractFilter):
    """A filter that just returns the value as-is. Used when you only want to specify a default value."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["value"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the value as-is."""
        return self.get_value()



class MapFilter(AbstractFilter):
    """A filter to display coordinates as an interactive Leaflet map widget."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["width", "height", "zoom", "marker", "popup", "groups", "colors", "legend"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns a Leaflet map widget HTML."""
        value = self.get_value()
        
        # Extract markers from various input formats
        markers = self.extract_markers(value)
        
        if not markers:
            if self.get_configuration("default"):
                # If no markers found, a default value might be specified
                return self.get_configuration("default")
            return f"<span class=\"text-muted\">No valid coordinates found: {value}</span>"
        
        # Generate unique ID for this map
        map_id = f"map_{uuid.uuid4().hex[:8]}"
        
        # Configuration
        width = self.get_configuration("width") or "300px"
        height = self.get_configuration("height") or "200px" 
        zoom = self.get_configuration("zoom") or "10"  # Lower default zoom for multiple markers
        show_marker = self.get_configuration("marker") != "false"
        show_legend = self.get_configuration("legend") != "false"  # Show legend by default
        
        # Calculate center and bounds for multiple markers
        if len(markers) == 1:
            center_lat, center_lng = markers[0]["latitude"], markers[0]["longitude"]
            fit_bounds = False
        else:
            center_lat = sum(m["latitude"] for m in markers) / len(markers)
            center_lng = sum(m["longitude"] for m in markers) / len(markers)
            fit_bounds = True
        
        # Generate markers JavaScript with colors
        markers_js = ""
        if show_marker:
            for i, marker in enumerate(markers):
                popup_text = marker.get("popup", f"Location {i+1}: {marker['latitude']}, {marker['longitude']}")
                color = marker.get("color", "red")
                
                # Properly escape quotes and newlines for JavaScript
                popup_text = popup_text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                
                # Create colored marker
                markers_js += f"""
                var icon_{i} = L.divIcon({{
                    className: 'custom-marker-{color}',
                    html: '<div style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.4);"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                }});
                L.marker([{marker["latitude"]}, {marker["longitude"]}], {{icon: icon_{i}}}).addTo(map).bindPopup("{popup_text}");
                """
        
        # Generate bounds JavaScript for multiple markers
        bounds_js = ""
        if fit_bounds and len(markers) > 1:
            bounds_coords = [[m["latitude"], m["longitude"]] for m in markers]
            bounds_js = f"var bounds = {json.dumps(bounds_coords)}; map.fitBounds(bounds, {{padding: [10, 10]}});"
        
        # Generate legend HTML
        legend_html = ""
        if show_legend and len(markers) > 1:
            # Get unique groups and colors
            groups = {}
            for marker in markers:
                group_name = marker.get("group", "default")
                group_color = marker.get("color", "red")
                if group_name not in groups:
                    groups[group_name] = group_color
            
            if len(groups) > 1:  # Only show legend if there are multiple groups
                legend_items = []
                for group_name, color in groups.items():
                    display_name = group_name.replace("_", " ").title() if group_name != "default" else "Location"
                    legend_items.append(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <div style="width: 12px; height: 12px; background-color: {color}; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.4); margin-right: 8px;"></div>
                        <span style="font-size: 12px; color: #333;">{display_name}</span>
                    </div>
                    """)
                
                legend_html = f"""
                <div style="background: white; border: 1px solid #ccc; border-radius: 4px; padding: 8px; margin-top: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                    <div style="font-size: 13px; font-weight: bold; margin-bottom: 6px; color: #555;">Legend</div>
                    {"".join(legend_items)}
                </div>
                """
        
        # Generate the HTML
        return f"""
        <div>
            <div id="{map_id}" style="width: {width}; height: {height}; border: 1px solid #ccc; border-radius: 4px;"></div>
            {legend_html}
        </div>
        <script>
        (function() {{
            // Load Leaflet if not already loaded
            if (typeof L === "undefined") {{
                var link = document.createElement("link");
                link.rel = "stylesheet";
                link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
                document.head.appendChild(link);
                
                var script = document.createElement("script");
                script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
                script.onload = function() {{ initMap_{map_id}(); }};
                document.head.appendChild(script);
            }} else {{
                initMap_{map_id}();
            }}
            
            function initMap_{map_id}() {{
                var map = L.map("{map_id}").setView([{center_lat}, {center_lng}], {zoom});
                
                L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
                    attribution: "&copy; OpenStreetMap contributors"
                }}).addTo(map);
                
                {markers_js}
                
                {bounds_js}
            }}
        }})();
        </script>
        """
    
    def extract_markers(self, value):
        """Extract multiple markers from various input formats."""
        markers = []
        groups_config = self.get_configuration("groups")
        default_colors = ["red", "blue", "green", "orange", "purple", "yellow", "pink", "gray"]
        
        if groups_config:
            # Handle groups configuration: "Founded:12321:red,Liquidated:12322:blue,Work:12331:green"
            groups = self.parse_groups_config(groups_config, value)
            for group in groups:
                group_markers = self.extract_group_markers(group["data"], group["name"], group["color"])
                markers.extend(group_markers)
        else:
            # Regular extraction for backward compatibility
            if isinstance(value, dict):
                # Check for direct latitude/longitude coordinates first
                if "latitude" in value and "longitude" in value:
                    # Single coordinate dict - create marker directly
                    try:
                        lat = float(value["latitude"])
                        lng = float(value["longitude"])

                        # Create popup with available info
                        popup_parts = []
                        if "name" in value:
                            popup_parts.append(f"Name: {value['name']}")
                        if "transcription" in value:
                            popup_parts.append(f"Transcription: {value['transcription']}")
                        popup_text = " | ".join(popup_parts) if popup_parts else f"Coordinates: {lat}, {lng}"

                        markers.append({
                            "latitude": lat,
                            "longitude": lng,
                            "popup": popup_text,
                            "group": "default",
                            "color": default_colors[0]
                        })
                    except (ValueError, TypeError):
                        pass  # Continue to other extraction methods
                # Check if this looks like object_subs structure with multiple groups
                elif all(isinstance(v, list) for v in value.values() if isinstance(v, (list, dict))):
                    is_object_subs = True
                else:
                    is_object_subs = False

                if "type" in value and "coordinates" in value:
                    # Single geometry object
                    lat, lng = self.extract_coordinates(value)
                    if lat is not None and lng is not None:
                        markers.append({
                            "latitude": lat,
                            "longitude": lng,
                            "popup": self.get_configuration("popup") or f"Coordinates: {lat}, {lng}",
                            "group": "default",
                            "color": default_colors[0]
                        })
                elif "geometry" in value:
                    # Single object with geometry field
                    marker = self.extract_single_marker(value, "0", "default", default_colors[0])
                    if marker:
                        markers.append(marker)
                elif is_object_subs:
                    # Auto-detect groups from object_subs structure
                    for i, (key, objects) in enumerate(value.items()):
                        color = default_colors[i % len(default_colors)]
                        group_markers = self.extract_group_markers(objects, key, color)
                        markers.extend(group_markers)
                else:
                    # Handle as regular dict
                    for key, objects in value.items():
                        if isinstance(objects, list):
                            for obj in objects:
                                marker = self.extract_single_marker(obj, key, "default", default_colors[0])
                                if marker:
                                    markers.append(marker)
                        else:
                            marker = self.extract_single_marker(objects, key, "default", default_colors[0])
                            if marker:
                                markers.append(marker)
            elif isinstance(value, list):
                # Direct list of objects
                for i, obj in enumerate(value):
                    marker = self.extract_single_marker(obj, str(i), "default", default_colors[0])
                    if marker:
                        markers.append(marker)
            else:
                # Single coordinates
                lat, lng = self.extract_coordinates(value)
                if lat is not None and lng is not None:
                    markers.append({
                        "latitude": lat,
                        "longitude": lng,
                        "popup": self.get_configuration("popup") or f"Coordinates: {lat}, {lng}",
                        "group": "default",
                        "color": default_colors[0]
                    })
        
        return markers
    
    def parse_groups_config(self, groups_config, data):
        """Parse groups configuration string."""
        groups = []
        if not isinstance(data, dict):
            return groups
        
        # Remove surrounding quotes if present
        if groups_config.startswith('"') and groups_config.endswith('"'):
            groups_config = groups_config[1:-1]
        elif groups_config.startswith("'") and groups_config.endswith("'"):
            groups_config = groups_config[1:-1]
            
        group_parts = groups_config.split(',')
        for part in group_parts:
            elements = part.strip().split(':')
            if len(elements) >= 2:
                name = elements[0].strip()
                key = elements[1].strip()
                color = elements[2].strip() if len(elements) > 2 else "red"
                
                if key in data:
                    groups.append({
                        "name": name,
                        "data": data[key],
                        "color": color
                    })
        return groups
    
    def extract_group_markers(self, data, group_name, color):
        """Extract markers for a specific group."""
        markers = []
        if isinstance(data, list):
            for i, obj in enumerate(data):
                marker = self.extract_single_marker(obj, f"{group_name}_{i}", group_name, color)
                if marker:
                    markers.append(marker)
        else:
            marker = self.extract_single_marker(data, group_name, group_name, color)
            if marker:
                markers.append(marker)
        return markers

    def extract_single_marker(self, obj, identifier, group="default", color="red"):
        """Extract a single marker from an object."""
        if not isinstance(obj, dict):
            return None
            
        # Look for geometry field first
        if "geometry" in obj and isinstance(obj["geometry"], dict):
            geometry = obj["geometry"]
            if "latitude" in geometry and "longitude" in geometry:
                try:
                    lat = float(geometry["latitude"])
                    lng = float(geometry["longitude"])
                    
                    # Create popup text with available info
                    popup_parts = []
                    if group != "default":
                        popup_parts.append(f"Type: {group}")
                    if "location" in obj and obj["location"]:
                        popup_parts.append(f"Location: {obj['location']}")
                    if "start" in obj and obj["start"]:
                        popup_parts.append(f"Start: {obj['start']}")
                    if "end" in obj and obj["end"]:
                        popup_parts.append(f"End: {obj['end']}")
                    
                    popup_text = " | ".join(popup_parts) if popup_parts else f"Point {identifier}"
                    
                    return {
                        "latitude": lat,
                        "longitude": lng,
                        "popup": popup_text,
                        "group": group,
                        "color": color
                    }
                except (ValueError, TypeError):
                    pass
        
        # Fallback to direct coordinate extraction
        lat, lng = self.extract_coordinates(obj)
        if lat is not None and lng is not None:
            return {
                "latitude": lat,
                "longitude": lng,
                "popup": f"Point {identifier}: {lat}, {lng}",
                "group": group,
                "color": color
            }
        
        return None
    
    def extract_coordinates(self, value):
        """Extract latitude and longitude from various input formats."""
        if isinstance(value, dict):
            # Handle geometry objects like from nodegoat
            if "latitude" in value and "longitude" in value:
                try:
                    return float(value["latitude"]), float(value["longitude"])
                except (ValueError, TypeError):
                    return None, None
            elif "coordinates" in value and isinstance(value["coordinates"], list) and len(value["coordinates"]) >= 2:
                try:
                    # GeoJSON format: [longitude, latitude]
                    return float(value["coordinates"][1]), float(value["coordinates"][0])
                except (ValueError, TypeError, IndexError):
                    return None, None
        elif isinstance(value, list) and len(value) >= 2:
            try:
                # Assume [latitude, longitude] or [longitude, latitude]
                # Try both orders and use the one that makes geographic sense
                lat1, lon1 = float(value[0]), float(value[1])
                lat2, lon2 = float(value[1]), float(value[0])
                
                # Check which interpretation makes more geographic sense
                if -90 <= lat1 <= 90 and -180 <= lon1 <= 180:
                    return lat1, lon1
                elif -90 <= lat2 <= 90 and -180 <= lon2 <= 180:
                    return lat2, lon2
                else:
                    return lat1, lon1  # Fallback to first interpretation
            except (ValueError, TypeError, IndexError):
                return None, None
        elif isinstance(value, str):
            # Try to parse coordinate strings like "47.5537, 8.0219"
            try:
                parts = value.replace(" ", "").split(",")
                if len(parts) == 2:
                    return float(parts[0]), float(parts[1])
            except (ValueError, IndexError):
                pass
        
        return None, None



class TextTruncateFilter(AbstractFilter):
    """A filter to truncate long text with optional expandable functionality."""

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["length", "expandable", "expand_text", "collapse_text", "ellipsis"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns truncated text with optional expand/collapse functionality."""
        import uuid
        import html

        value = self.get_value()
        if not value:
            return ""

        text = str(value).strip()
        if not text:
            return ""

        # Configuration
        max_length = int(self.get_configuration("length") or 200)
        is_expandable = self.get_configuration("expandable") != "false"  # Default to true
        expand_text = self.get_configuration("expand_text") or "Show more"
        collapse_text = self.get_configuration("collapse_text") or "Show less"
        ellipsis = self.get_configuration("ellipsis") or "..."

        # If text is short enough, return as-is
        if len(text) <= max_length:
            return f"<span>{html.escape(text)}</span>"

        # Truncate text at word boundary if possible
        truncated = text[:max_length]
        if " " in text[max_length:max_length+20]:  # Look ahead for word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_length * 0.8:  # Only use word boundary if not too far back
                truncated = truncated[:last_space]

        # Escape HTML in text
        truncated_escaped = html.escape(truncated)
        full_text_escaped = html.escape(text)

        if not is_expandable:
            # Non-expandable: just return truncated text with ellipsis
            return f"<span>{truncated_escaped}{ellipsis}</span>"

        # Expandable: create interactive version
        unique_id = f"text_{uuid.uuid4().hex[:8]}"

        return f"""
        <span id="{unique_id}_container">
            <span id="{unique_id}_truncated">{truncated_escaped}{ellipsis}
                <a href="#" id="{unique_id}_expand" style="color: #007bff; text-decoration: none; font-size: 0.9em; cursor: pointer;">{expand_text}</a>
            </span>
            <span id="{unique_id}_full" style="display: none;">{full_text_escaped}
                <a href="#" id="{unique_id}_collapse" style="color: #007bff; text-decoration: none; font-size: 0.9em; cursor: pointer;">{collapse_text}</a>
            </span>
        </span>
        <script>
        (function() {{
            var expandBtn = document.getElementById("{unique_id}_expand");
            var collapseBtn = document.getElementById("{unique_id}_collapse");
            var truncatedSpan = document.getElementById("{unique_id}_truncated");
            var fullSpan = document.getElementById("{unique_id}_full");

            if (expandBtn) {{
                expandBtn.addEventListener("click", function(e) {{
                    e.preventDefault();
                    truncatedSpan.style.display = "none";
                    fullSpan.style.display = "inline";
                }});
            }}

            if (collapseBtn) {{
                collapseBtn.addEventListener("click", function(e) {{
                    e.preventDefault();
                    fullSpan.style.display = "none";
                    truncatedSpan.style.display = "inline";
                }});
            }}
        }})();
        </script>
        """


class ReadableNumberFilter(AbstractFilter):
    """A filter to format numbers with separators for better readability.

    Usage: [number|readable(separator="'")]
    Examples:
        123456 -> 123'456
        1234567890 -> 1'234'567'890
        With separator=",": 123456 -> 123,456
    """

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["separator"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the formatted number with separators."""
        try:
            value = self.get_value()
            separator = self.get_configuration("separator") or "'"

            # Convert to int/float if it's a string
            if isinstance(value, str):
                value = float(value) if '.' in value else int(value)

            # Split into integer and decimal parts
            if isinstance(value, float):
                int_part, dec_part = str(value).split('.')
                formatted_int = "{:,}".format(int(int_part)).replace(',', separator)
                return f"{formatted_int}.{dec_part}"
            else:
                return "{:,}".format(int(value)).replace(',', separator)
        except (ValueError, TypeError, AttributeError):
            return self.get_value()


class CompactNumberFilter(AbstractFilter):
    """A filter to format numbers in compact form (K for thousands, M for millions).

    Usage: [number|compact(precision="1")]
    Examples:
        21438 -> 21.4K
        1234567 -> 1.2M
        123 -> 123
        With precision=0: 21438 -> 21K
    """

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["precision"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the formatted number in compact form."""
        try:
            value = self.get_value()
            precision = int(self.get_configuration("precision") or 1)

            # Convert to number if it's a string
            if isinstance(value, str):
                value = float(value) if '.' in value else int(value)

            num = float(value)

            if abs(num) >= 1_000_000_000:
                formatted = f"{num / 1_000_000_000:.{precision}f}B"
            elif abs(num) >= 1_000_000:
                formatted = f"{num / 1_000_000:.{precision}f}M"
            elif abs(num) >= 1_000:
                formatted = f"{num / 1_000:.{precision}f}K"
            else:
                return str(int(num) if num == int(num) else num)

            # Remove trailing zeros after decimal point
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')

            return formatted
        except (ValueError, TypeError, AttributeError):
            return self.get_value()


class RelativeDateFilter(AbstractFilter):
    """A filter to format dates as relative time (e.g., 'today', 'yesterday', '2 days ago').

    Usage: [date|relative()]
    Examples:
        Today's date -> "today"
        Yesterday -> "yesterday"
        2 days ago -> "2 days ago"
        Last week -> "1 week ago"
        Older dates -> formatted as "13.10.2025"
    """

    def needed_attributes(self):
        return []

    def allowed_attributes(self):
        return ["format"]

    def needed_options(self):
        return []

    def get_rendered_value(self):
        """Returns the date formatted as relative time."""
        from django.utils import timezone

        try:
            value = self.get_value()

            # Parse the date if it's a string
            if isinstance(value, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        date_obj = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return self.get_value()  # If no format matches, return original
            elif isinstance(value, datetime):
                date_obj = value.date()
            elif hasattr(value, 'year'):  # date object
                date_obj = value
            else:
                return self.get_value()

            # Get today's date (timezone-aware if needed)
            today = timezone.now().date() if timezone.is_aware(timezone.now()) else datetime.now().date()

            # Calculate difference
            diff = (today - date_obj).days

            if diff == 0:
                return "today"
            elif diff == 1:
                return "yesterday"
            elif diff == -1:
                return "tomorrow"
            elif diff > 1 and diff < 7:
                return f"{diff} days ago"
            elif diff == 7:
                return "1 week ago"
            elif diff > 7 and diff < 30:
                weeks = diff // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif diff >= 30 and diff < 365:
                months = diff // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            elif diff >= 365:
                years = diff // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
            elif diff < -1 and diff > -7:
                return f"in {abs(diff)} days"
            elif diff <= -7 and diff > -30:
                weeks = abs(diff) // 7
                return f"in {weeks} week{'s' if weeks > 1 else ''}"
            else:
                # For older dates or far future dates, return formatted date
                format_str = self.get_configuration("format") or "%d.%m.%Y"
                return date_obj.strftime(format_str)
        except (ValueError, TypeError, AttributeError):
            return self.get_value()
