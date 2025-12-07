"""Management command to update file upload objects."""
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from ndr_core.models import NdrCoreUpload


class Command(BaseCommand):
    """Update file upload objects (replace file or update metadata)."""

    help = 'Updates file upload objects (replace file or update metadata)'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'upload_id',
            nargs='?',
            type=int,
            help='ID of the upload object to update'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Path to new file to replace the existing one'
        )
        parser.add_argument(
            '--title',
            type=str,
            help='New title for the upload'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all upload objects'
        )
        parser.add_argument(
            '--show',
            type=int,
            help='Display information about a specific upload object'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # Handle --list flag
        if options['list']:
            self._list_uploads()
            return

        # Handle --show flag
        if options['show']:
            self._show_upload(options['show'])
            return

        # Validate required arguments
        if not options['upload_id']:
            raise CommandError('upload_id is required (or use --list to see all uploads)')

        upload_id = options['upload_id']

        # Check that at least one update option is provided
        if not options['file'] and not options['title']:
            raise CommandError(
                'At least one of --file or --title must be provided '
                '(or use --show <id> to display upload info)'
            )

        # Perform update
        self._update_upload(upload_id, options['file'], options['title'])

    def _list_uploads(self):
        """List all upload objects."""
        uploads = NdrCoreUpload.objects.all().order_by('-id')

        if not uploads:
            self.stdout.write(self.style.WARNING('No upload objects found'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {uploads.count()} upload objects:'))
        self.stdout.write('')

        for upload in uploads:
            file_name = os.path.basename(upload.file.name) if upload.file else '(no file)'
            title = upload.title if upload.title else '(no title)'

            self.stdout.write(f'  ID: {upload.id}')
            self.stdout.write(f'    Title: {title}')
            self.stdout.write(f'    File: {file_name}')

            if upload.file:
                self.stdout.write(f'    Type: {upload.get_file_type()}')
                self.stdout.write(f'    Size: {upload.get_file_size_display()}')

            self.stdout.write('')

    def _show_upload(self, upload_id):
        """Display detailed information about an upload object."""
        try:
            upload = NdrCoreUpload.objects.get(pk=upload_id)

            self.stdout.write(f'Upload ID: {upload.id}')
            self.stdout.write(f'Title: {upload.title if upload.title else "(no title)"}')

            if upload.file:
                self.stdout.write(f'File name: {os.path.basename(upload.file.name)}')
                self.stdout.write(f'File path: {upload.file.name}')
                self.stdout.write(f'File type: {upload.get_file_type()}')
                self.stdout.write(f'Extension: {upload.get_file_extension()}')
                self.stdout.write(f'Size: {upload.get_file_size_display()} ({upload.get_file_size()} bytes)')
                self.stdout.write(f'Icon class: {upload.get_file_icon_class()}')
            else:
                self.stdout.write(self.style.WARNING('No file associated'))

        except NdrCoreUpload.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Upload object with ID {upload_id} does not exist'))
            raise CommandError(f'Upload object {upload_id} not found')

    def _update_upload(self, upload_id, file_path, title):
        """Update an upload object."""
        try:
            upload = NdrCoreUpload.objects.get(pk=upload_id)

            changes = []

            # Update title if provided
            if title is not None:
                old_title = upload.title if upload.title else '(empty)'
                upload.title = title
                changes.append(f'title: "{old_title}" -> "{title}"')

            # Update file if provided
            if file_path:
                # Validate file exists
                if not os.path.isfile(file_path):
                    self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
                    raise CommandError(f'File does not exist: {file_path}')

                # Get old file info before replacement
                old_file_name = os.path.basename(upload.file.name) if upload.file else '(no file)'

                # Open and save the new file
                with open(file_path, 'rb') as f:
                    django_file = File(f, name=os.path.basename(file_path))
                    upload.file.save(os.path.basename(file_path), django_file, save=False)

                new_file_name = os.path.basename(file_path)
                changes.append(f'file: "{old_file_name}" -> "{new_file_name}"')

            # Save the upload object
            upload.save()

            # Report changes
            self.stdout.write(self.style.SUCCESS(f'Updated upload {upload_id}:'))
            for change in changes:
                self.stdout.write(f'  {change}')

            # Display updated info
            if file_path:
                self.stdout.write(f'New file size: {upload.get_file_size_display()}')
                self.stdout.write(f'New file type: {upload.get_file_type()}')

        except NdrCoreUpload.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Upload object with ID {upload_id} does not exist'))
            raise CommandError(f'Upload object {upload_id} not found')
        except IOError as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {str(e)}'))
            raise CommandError(f'Error reading file: {str(e)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating upload: {str(e)}'))
            raise CommandError(f'Error updating upload: {str(e)}')
