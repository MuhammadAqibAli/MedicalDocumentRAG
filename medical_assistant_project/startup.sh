#!/bin/bash

# Navigate to the folder
cd /home/site/wwwroot

# Create a virtual environment (optional but good)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start Gunicorn for Django
gunicorn medical_assistant_project.wsgi --bind=0.0.0.0 --timeout 600