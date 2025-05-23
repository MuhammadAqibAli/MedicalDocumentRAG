import os
import sys
import django

# Set environment variables
os.environ.setdefault('APP_ENV', 'development')
os.environ.setdefault('SECRET_KEY', 'django-insecure-development-key-for-testing-only')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_assistant_project.settings')

# Initialize Django
django.setup()

# Import Django models and migration utilities
from django.core.management import call_command

# Generate migrations
call_command('makemigrations')
print("Migrations generated successfully!")
