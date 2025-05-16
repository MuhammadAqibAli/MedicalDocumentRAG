FROM python:3.13.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Install Python dependencies
COPY ./medical_assistant_project/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn  # Explicitly install gunicorn

# Copy project
COPY . /app/

# Copy .env file
COPY ./medical_assistant_project/.env /app/.env

# Collect static files
WORKDIR /app/medical_assistant_project
RUN python manage.py collectstatic --noinput

# Run the app
CMD ["python", "-m", "gunicorn", "medical_assistant_project.wsgi:application", "--bind", "0.0.0.0:8000"]


