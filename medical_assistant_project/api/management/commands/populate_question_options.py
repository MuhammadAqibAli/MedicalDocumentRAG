from django.core.management.base import BaseCommand
from api.models import QuestionOption

class Command(BaseCommand):
    help = 'Populates the QuestionOption table with predefined options'

    def handle(self, *args, **options):
        # Define the options to be added
        options_data = [
            {"label": "Compliant", "property": "Compliant"},
            {"label": "Full compliant", "property": "Full compliant"},
            {"label": "Fully Satisfied", "property": "Fully Satisfied"},
            {"label": "Partial Compliant", "property": "Partial Compliant"},
            {"label": "Non Compliant", "property": "Non Compliant"},
        ]

        # Count how many options were added
        added_count = 0

        # Add each option to the database
        for option_data in options_data:
            # Check if the option already exists
            option, created = QuestionOption.objects.get_or_create(
                label=option_data["label"],
                defaults={"property": option_data["property"]}
            )

            if created:
                added_count += 1
                self.stdout.write(self.style.SUCCESS(f'Added option: {option.label}'))
            else:
                self.stdout.write(self.style.WARNING(f'Option already exists: {option.label}'))

        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Successfully added {added_count} new options'))
