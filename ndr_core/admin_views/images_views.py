"""Views for the images section in the admin panel. """
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView

from ndr_core.admin_forms.images_forms import ImageUploadForm, ImageEditForm
from ndr_core.admin_views.admin_views import AdminViewMixin
from ndr_core.models import NdrCoreImage


class ConfigureImages(AdminViewMixin, LoginRequiredMixin, View):
    """Image library view - shows all images in a grid with upload/edit/delete functionality. """

    def get(self, request, *args, **kwargs):
        """GET request for this view. """
        images = NdrCoreImage.objects.filter(image_active=True)
        context = {'images': images}
        return render(self.request,
                      template_name='ndr_core/admin_views/overview/configure_images.html',
                      context=context)


class ImagesUploadView(AdminViewMixin, LoginRequiredMixin, CreateView):
    """ View to upload a new image to the library """

    model = NdrCoreImage
    form_class = ImageUploadForm
    success_url = reverse_lazy('ndr_core:configure_images')
    template_name = 'ndr_core/admin_views/create/image_upload.html'


class ImagesEditView(AdminViewMixin, LoginRequiredMixin, UpdateView):
    """ View to edit an existing image """

    model = NdrCoreImage
    form_class = ImageEditForm
    success_url = reverse_lazy('ndr_core:configure_images')
    template_name = 'ndr_core/admin_views/edit/image_edit.html'


class ImagesDeleteView(AdminViewMixin, LoginRequiredMixin, DeleteView):
    """ View to delete an image from the library. Asks to confirm.
    File deletion is handled automatically by the signal. """

    model = NdrCoreImage
    success_url = reverse_lazy('ndr_core:configure_images')
    template_name = 'ndr_core/admin_views/delete/image_confirm_delete.html'
