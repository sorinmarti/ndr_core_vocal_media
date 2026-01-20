"""Form to configure data list filters for a search configuration."""
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div
from django import forms

from ndr_core.models import NdrCoreSearchField


class DataListFiltersEditForm(forms.Form):
    """Form to select which search fields should be used as data list filters."""

    data_list_filters = forms.ModelMultipleChoiceField(
        queryset=NdrCoreSearchField.objects.all().order_by('field_label'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select search fields to use as pre-filters for data list pages. "
                  "Their initial values will be automatically applied."
    )

    @property
    def helper(self):
        """Creates and returns the form helper property."""
        helper = FormHelper()
        helper.form_method = "POST"
        layout = helper.layout = Layout()

        # Add info message
        layout.append(
            Div(
                HTML(
                    '<div class="alert alert-info">'
                    '<i class="fa-regular fa-circle-info"></i> '
                    '<strong>Data List Filters:</strong> Select search fields that will be '
                    'automatically applied as filters on data list pages. The initial values '
                    'configured in each search field will be used. This is useful for pre-filtering '
                    'data lists to show only specific subsets of data.'
                    '</div>'
                ),
                css_class='mb-3'
            )
        )

        # Add the checkbox field
        layout.append('data_list_filters')

        # Add submit button
        layout.append(
            Div(
                Submit('submit', 'Save Data List Filters', css_class='btn-primary'),
                css_class='mt-3'
            )
        )

        return helper
