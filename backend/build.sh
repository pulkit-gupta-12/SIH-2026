#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# Run database migrations against Neon
python manage.py migrate

# Create the predefined roles and demo accounts used by the login page.
# The command is idempotent, so it is safe to run on every deployment.
python manage.py seed_roles
