#!/bin/bash
# Gunicorn command to start the Django application
# Make sure medical_assistant_project.wsgi is the correct path to your WSGI application
gunicorn --bind=0.0.0.0 --timeout 600 medical_assistant_project.wsgi