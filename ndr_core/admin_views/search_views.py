"""Views for the search configuration pages. """
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, FormView

from ndr_core.admin_forms.search_config_forms import (
    SearchConfigurationCreateForm,
    SearchConfigurationEditForm
)
from ndr_core.admin_forms.search_form_forms import SearchConfigurationFormEditForm
from ndr_core.admin_forms.data_list_filter_forms import DataListFiltersEditForm
from ndr_core.admin_views.admin_views import AdminViewMixin
from ndr_core.models import (
    NdrCoreSearchField,
    NdrCoreSearchConfiguration,
    NdrCoreSearchFieldFormConfiguration,
    NdrCoreResultField
)


class ConfigureSearch(AdminViewMixin, LoginRequiredMixin, View):
    """View to add/edit/delete Search configurations. """

    def get(self, request, *args, **kwargs):
        """GET request for this view. """

        search_fields = NdrCoreSearchField.objects.all().order_by('field_label')
        result_fields = NdrCoreResultField.objects.all().order_by('label')
        searches = NdrCoreSearchConfiguration.objects.all()

        # Build a mapping of which search configurations use each search field
        search_field_usage = {}
        for field in search_fields:
            # Find all SearchFieldFormConfigurations that use this field
            form_configs = NdrCoreSearchFieldFormConfiguration.objects.filter(search_field=field)
            # Find all SearchConfigurations that use these form configs
            used_by = []
            for search_config in searches:
                if search_config.search_form_fields.filter(search_field=field).exists():
                    used_by.append(search_config)
            search_field_usage[field.pk] = used_by

        # Build a mapping of which search configurations use each result field
        result_field_usage = {}
        for field in result_fields:
            # Find all SearchConfigurations that use this result field
            used_by = []
            for search_config in searches:
                if search_config.result_card_fields.filter(result_field=field).exists():
                    used_by.append(search_config)
            result_field_usage[field.pk] = used_by

        context = {'search_fields': search_fields,
                   'result_fields': result_fields,
                   'searches': searches,
                   'search_field_usage': search_field_usage,
                   'result_field_usage': result_field_usage}

        return render(self.request, template_name='ndr_core/admin_views/overview/configure_search.html',
                      context=context)


class SearchConfigurationCreateView(AdminViewMixin, LoginRequiredMixin, CreateView):
    """ View to create a new API configuration """

    model = NdrCoreSearchConfiguration

    form_class = SearchConfigurationCreateForm
    success_url = reverse_lazy('ndr_core:configure_search')
    template_name = 'ndr_core/admin_views/create/search_config_create.html'


class SearchConfigurationEditView(AdminViewMixin, LoginRequiredMixin, UpdateView):
    """ View to edit an existing API configuration """

    model = NdrCoreSearchConfiguration
    form_class = SearchConfigurationEditForm
    success_url = reverse_lazy('ndr_core:configure_search')
    template_name = 'ndr_core/admin_views/edit/search_config_edit.html'


class SearchConfigurationDeleteView(AdminViewMixin, LoginRequiredMixin, DeleteView):
    """ View to delete a Search Field from the database. Asks to confirm."""

    model = NdrCoreSearchConfiguration
    success_url = reverse_lazy('ndr_core:configure_search')
    template_name = 'ndr_core/admin_views/delete/search_config_confirm_delete.html'


class SearchConfigurationCopyView(AdminViewMixin, LoginRequiredMixin, View):
    """ View to copy a Search configuration. """

    def get(self, request, *args, **kwargs):
        """GET request for this view. """

        search_conf = NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk'])
        search_conf.conf_name = f'{search_conf.conf_name}_copy'
        search_conf.conf_label = f'{search_conf.conf_label} (Copy)'
        search_conf.save()

        return redirect('ndr_core:configure_search')


class SearchConfigurationFormEditView(AdminViewMixin, LoginRequiredMixin, FormView):
    """ View to edit the form configuration for a search configuration. """

    form_class = SearchConfigurationFormEditForm
    template_name = 'ndr_core/admin_views/edit/search_form_edit.html'
    success_url = reverse_lazy('ndr_core:configure_search')

    def get_form(self, form_class=None):
        """Returns the form for this view. """
        form = super().get_form(form_class=form_class)
        fields = (NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk']).search_form_fields.all().
                  order_by('field_column').order_by('field_row'))

        form_row = 0
        for field in fields:
            form.fields[f'search_field_{form_row}'].initial = field.search_field
            form.fields[f'row_field_{form_row}'].initial = field.field_row
            form.fields[f'column_field_{form_row}'].initial = field.field_column
            form.fields[f'size_field_{form_row}'].initial = field.field_size
            form_row += 1

        return form

    @staticmethod
    def get_row_fields(row):
        """Returns the field names for a given row. """
        return [f'search_field_{row}', f'row_field_{row}', f'column_field_{row}', f'size_field_{row}']

    def form_valid(self, form):
        """Creates or updates the form configuration for a search configuration. """
        response = super().form_valid(form)
        conf_object = NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk'])

        for row in range(20):
            fields = self.get_row_fields(row)
            if all(field in form.cleaned_data for field in fields) and \
                    all(form.cleaned_data[x] is not None for x in fields):

                # There is a valid row of configuration. Check if it already exists in the database.
                try:
                    updatable_obj = (
                        conf_object.search_form_fields.get(search_field=form.cleaned_data[f'search_field_{row}']))
                    updatable_obj.field_row = form.cleaned_data[f'row_field_{row}']
                    updatable_obj.field_column = form.cleaned_data[f'column_field_{row}']
                    updatable_obj.field_size = form.cleaned_data[f'size_field_{row}']
                    updatable_obj.save()
                except NdrCoreSearchFieldFormConfiguration.DoesNotExist:
                    new_field = NdrCoreSearchFieldFormConfiguration.objects.create(
                        search_field=form.cleaned_data[f'search_field_{row}'],
                        field_row=form.cleaned_data[f'row_field_{row}'],
                        field_column=form.cleaned_data[f'column_field_{row}'],
                        field_size=form.cleaned_data[f'size_field_{row}'])
                    conf_object.search_form_fields.add(new_field)
        return response


class DataListFiltersEditView(AdminViewMixin, LoginRequiredMixin, FormView):
    """View to configure data list filters for a search configuration."""

    form_class = DataListFiltersEditForm
    template_name = 'ndr_core/admin_views/edit/data_list_filters_edit.html'
    success_url = reverse_lazy('ndr_core:configure_search')

    def get_form(self, form_class=None):
        """Returns the form with initial data from the search configuration."""
        form = super().get_form(form_class=form_class)
        search_config = NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk'])

        # Set initial selected filters
        form.fields['data_list_filters'].initial = search_config.data_list_filters.all()

        return form

    def get_context_data(self, **kwargs):
        """Add search configuration to context."""
        context = super().get_context_data(**kwargs)
        context['search_config'] = NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        """Save the selected data list filters to the search configuration."""
        response = super().form_valid(form)
        search_config = NdrCoreSearchConfiguration.objects.get(pk=self.kwargs['pk'])

        # Update the data list filters
        search_config.data_list_filters.set(form.cleaned_data['data_list_filters'])

        return response
