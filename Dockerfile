FROM python:3.13.3-slim

# Set environment variables for Python behavior
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Build-time Arguments for settings needed by collectstatic ---
ARG DJANGO_SECRET_KEY_BUILD="dummy-build-time-secret-key-for-collectstatic"
ARG DJANGO_DEBUG_BUILD="False"
# Add other ARGs here if collectstatic specifically needs them (e.g., STATIC_ROOT if configured via ENV)
# ARG DJANGO_STATIC_ROOT_BUILD="/app/staticfiles"

# --- Set ENVs from ARGs for the build phase ---
# These will be used by 'collectstatic'
ENV SECRET_KEY=${DJANGO_SECRET_KEY_BUILD}
ENV DEBUG=${DJANGO_DEBUG_BUILD}
# If you added STATIC_ROOT ARG:
# ENV STATIC_ROOT=${DJANGO_STATIC_ROOT_BUILD}

# Set work directory
WORKDIR /app

# Install system dependencies needed for some Python packages (like psycopg2)
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements.txt first to leverage Docker layer caching
COPY ./medical_assistant_project/requirements.txt /app/medical_assistant_project/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/medical_assistant_project/requirements.txt
RUN pip install --no-cache-dir gunicorn # Explicitly install gunicorn

# Copy the entire project
# Ensure your .dockerignore file excludes .git, venv, __pycache__, etc.
COPY . /app/

# Collect static files
# This will use the SECRET_KEY and DEBUG values set from the ARGs above
WORKDIR /app/medical_assistant_project # Ensure this is where manage.py is located
RUN python manage.py collectstatic --noinput

# --- Unset build-time specific ENVs if you want to be super clean, though runtime ENVs will override ---
# ENV SECRET_KEY=""
# ENV DEBUG=""

# The CMD will use RUNTIME environment variables provided by Azure App Service
# EXPOSE 8000 # Good practice if you are also running locally
CMD ["python", "-m", "gunicorn", "medical_assistant_project.wsgi:application", "--bind", "0.0.0.0:8000"]