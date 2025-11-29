#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files (images/css for admin)
python manage.py collectstatic --no-input

# Update database schema
python manage.py migrate