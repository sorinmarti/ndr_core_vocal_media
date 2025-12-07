"""Management command to update search field dropdown values."""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from ndr_core.models import NdrCoreSearchField


class Command(BaseCommand):
    """Update search field dropdown values (list_choices)."""

    help = 'Updates search field dropdown values (list_choices JSON)'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'field_name',
            nargs='?',
            type=str,
            help='Name of the search field to update'
        )
        parser.add_argument(
            '--list-choices',
            type=str,
            help='JSON string or path to JSON file with dropdown choices'
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Display current dropdown values'
        )
        parser.add_argument(
            '--list-fields',
            action='store_true',
            help='List all search fields'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # Handle --list-fields flag
        if options['list_fields']:
            self._list_fields()
            return

        # Validate required arguments
        if not options['field_name']:
            raise CommandError('field_name is required (or use --list-fields to see all fields)')

        field_name = options['field_name']

        # Handle --show-current flag
        if options['show_current']:
            self._show_current(field_name)
            return

        # Validate list-choices argument for update operation
        if not options['list_choices']:
            raise CommandError(
                'list-choices is required for update operation '
                '(or use --show-current to display current values)'
            )

        list_choices = options['list_choices']

        # Perform update
        self._update_field(field_name, list_choices)

    def _list_fields(self):
        """List all search fields."""
        fields = NdrCoreSearchField.objects.all().order_by('field_name')

        if not fields:
            self.stdout.write(self.style.WARNING('No search fields found'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {fields.count()} search fields:'))
        self.stdout.write('')

        for field in fields:
            self.stdout.write(f'  {field.field_name}')
            self.stdout.write(f'    Type: {field.get_field_type_display()}')
            self.stdout.write(f'    Label: {field.field_label}')

            if field.is_choice_field():
                choices = field.get_choices_list()
                self.stdout.write(f'    Dropdown options: {len(choices)}')

            self.stdout.write('')

    def _show_current(self, field_name):
        """Display current dropdown values for a field."""
        try:
            field = NdrCoreSearchField.objects.get(pk=field_name)

            self.stdout.write(f'Field: {field.field_name}')
            self.stdout.write(f'Type: {field.get_field_type_display()}')
            self.stdout.write(f'Label: {field.field_label}')
            self.stdout.write('')

            if not field.is_choice_field():
                self.stdout.write(
                    self.style.WARNING('This field is not a choice field (LIST/MULTI_LIST/BOOLEAN_LIST)')
                )
                return

            self.stdout.write('Current dropdown values:')
            self.stdout.write('')

            # Display raw JSON
            if field.list_choices:
                try:
                    choices = json.loads(field.list_choices)
                    self.stdout.write(json.dumps(choices, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR('Invalid JSON in list_choices field'))
                    self.stdout.write(field.list_choices)
            else:
                self.stdout.write('(empty)')

        except NdrCoreSearchField.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Search field "{field_name}" does not exist'))
            raise CommandError(f'Search field "{field_name}" not found')

    def _update_field(self, field_name, list_choices):
        """Update the list_choices for a search field."""
        try:
            field = NdrCoreSearchField.objects.get(pk=field_name)

            # Check if field is a choice field
            if not field.is_choice_field():
                self.stdout.write(
                    self.style.WARNING(
                        f'Field type is {field.get_field_type_display()}. '
                        'Dropdown values only apply to LIST, MULTI_LIST, or BOOLEAN_LIST fields.'
                    )
                )

            # Parse JSON (from string or file)
            choices_data = self._parse_json_input(list_choices)

            # Validate JSON structure
            self._validate_choices_structure(choices_data)

            # Convert to JSON string
            json_string = json.dumps(choices_data, ensure_ascii=False)

            # Store old value for reporting
            old_choices_count = 0
            if field.list_choices:
                try:
                    old_choices = json.loads(field.list_choices)
                    old_choices_count = len(old_choices)
                except json.JSONDecodeError:
                    pass

            # Update the field
            field.list_choices = json_string
            field.save()

            new_choices_count = len(choices_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {field_name}: {old_choices_count} -> {new_choices_count} dropdown options'
                )
            )

        except NdrCoreSearchField.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Search field "{field_name}" does not exist'))
            raise CommandError(f'Search field "{field_name}" not found')
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {str(e)}'))
            raise CommandError(f'Invalid JSON format: {str(e)}')
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'Validation error: {str(e)}'))
            raise CommandError(str(e))

    def _parse_json_input(self, input_string):
        """Parse JSON from string or file path."""
        # Check if input is a file path
        if os.path.isfile(input_string):
            try:
                with open(input_string, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f'Invalid JSON in file {input_string}: {str(e)}')
            except IOError as e:
                raise ValueError(f'Error reading file {input_string}: {str(e)}')
        else:
            # Parse as JSON string
            try:
                return json.loads(input_string)
            except json.JSONDecodeError as e:
                raise ValueError(f'Invalid JSON string: {str(e)}')

    def _validate_choices_structure(self, choices_data):
        """Validate the structure of choices JSON."""
        if not isinstance(choices_data, list):
            raise ValueError('list_choices must be a JSON array')

        if len(choices_data) == 0:
            raise ValueError('list_choices array cannot be empty')

        # Validate each choice object
        for idx, choice in enumerate(choices_data):
            if not isinstance(choice, dict):
                raise ValueError(f'Choice at index {idx} must be an object/dict')

            # Required fields
            if 'key' not in choice:
                raise ValueError(f'Choice at index {idx} missing required field "key"')

            if 'value' not in choice:
                raise ValueError(f'Choice at index {idx} missing required field "value"')

            # Validate key and value are strings
            if not isinstance(choice['key'], str):
                raise ValueError(f'Choice at index {idx}: "key" must be a string')

            if not isinstance(choice['value'], str):
                raise ValueError(f'Choice at index {idx}: "value" must be a string')

            # Optional fields validation
            if 'initial' in choice:
                valid_initial = ['true', 'false', True, False]
                if choice['initial'] not in valid_initial:
                    raise ValueError(
                        f'Choice at index {idx}: "initial" must be "true" or "false"'
                    )

        self.stdout.write(f'Validated {len(choices_data)} dropdown choices')
