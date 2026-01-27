"""Custom widgets for admin forms."""
import json
from django import forms
from django.utils.safestring import mark_safe
from ndr_core.models import NdrCoreResultField


class TabChildrenWidget(forms.Widget):
    """Custom widget for managing tab children with a user-friendly interface."""

    template_name = 'ndr_core/widgets/tab_children_widget.html'

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget as HTML."""
        if attrs is None:
            attrs = {}

        attrs['class'] = attrs.get('class', '') + ' tab-children-input'
        attrs['style'] = 'display: none;'  # Hide the actual input

        # Fetch result fields fresh on each render to include newly created fields
        # Exclude tab containers to prevent nesting tabs in tabs
        result_fields = list(NdrCoreResultField.objects.filter(is_tab_container=False).order_by('label'))

        # Parse existing value
        tabs = []
        if value:
            try:
                if isinstance(value, str):
                    tabs = json.loads(value)
                elif isinstance(value, list):
                    tabs = value
            except (json.JSONDecodeError, TypeError):
                tabs = []

        # Build the HTML
        html = f'<input type="hidden" name="{name}" id="id_{name}" value=\'{json.dumps(tabs) if tabs else "[]"}\' {self.build_attrs(attrs)}>'

        html += '<div class="tab-children-widget" data-input-id="id_' + name + '">'
        html += '<table class="table table-sm table-bordered">'
        html += '<thead><tr>'
        html += '<th style="width: 5%">#</th>'
        html += '<th style="width: 30%">Tab Label</th>'
        html += '<th style="width: 45%">Result Field</th>'
        html += '<th style="width: 10%">Order</th>'
        html += '<th style="width: 10%">Action</th>'
        html += '</tr></thead>'
        html += '<tbody class="tab-rows">'

        # Add existing rows
        for idx, tab in enumerate(tabs):
            html += self._render_row(idx, tab, result_fields)

        # Add one empty row if no tabs exist
        if not tabs:
            html += self._render_row(0, {}, result_fields)

        html += '</tbody>'
        html += '</table>'
        html += '<button type="button" class="btn btn-sm btn-success add-tab-row">'
        html += '<i class="fa-regular fa-plus"></i> Add Tab</button>'
        html += '</div>'

        return mark_safe(html)

    def _render_row(self, idx, tab_data, result_fields):
        """Render a single row."""
        tab_label = tab_data.get('tab_label', '')
        result_field_id = tab_data.get('result_field_id', '')
        tab_order = tab_data.get('tab_order', idx + 1)

        html = '<tr class="tab-row">'
        html += f'<td class="text-center">{idx + 1}</td>'
        html += f'<td><input type="text" class="form-control form-control-sm tab-label" value="{tab_label}" placeholder="Tab Label"></td>'
        html += '<td><select class="form-control form-control-sm result-field-select">'
        html += '<option value="">-- Select Result Field --</option>'

        for field in result_fields:
            selected = 'selected' if str(field.id) == str(result_field_id) else ''
            field_label = field.label if field.label else str(field)
            html += f'<option value="{field.id}" {selected}>{field_label} (ID: {field.id})</option>'

        html += '</select></td>'
        html += f'<td><input type="number" class="form-control form-control-sm tab-order" value="{tab_order}" min="1"></td>'
        html += '<td class="text-center">'
        html += '<button type="button" class="btn btn-sm btn-danger remove-tab-row">'
        html += '<i class="fa-regular fa-trash"></i></button></td>'
        html += '</tr>'

        return html
