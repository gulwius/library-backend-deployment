#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# --- ADD THIS LINE TO CREATE SUPERUSER AUTOMATICALLY ---
# The "|| true" part prevents the deploy from failing if the user already exists
python manage.py createsuperuser --noinput || true