# Create a file in api/migrations/ with a name like 0003_rename_document_type_to_standard_type.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_document_document_type'),  # Replace with your actual previous migration
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='document_type',
            new_name='standard_type',
        ),
    ]