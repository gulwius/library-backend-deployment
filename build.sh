#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create superuser (if not exists)
python manage.py createsuperuser --noinput || true

# --- ADD THIS LINE ---
python manage.py setup_admin_otp