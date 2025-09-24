#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Compile translation files (skip if .po files don't exist or are corrupt)
echo "Checking for translation files..."
if [ -f "locale/it/LC_MESSAGES/django.po" ] && [ -f "locale/en/LC_MESSAGES/django.po" ]; then
    echo "Compiling translation messages..."
    python manage.py compilemessages --ignore=venv || echo "Warning: Could not compile messages, continuing..."
else
    echo "Translation files not found, skipping compilation..."
fi

# Create superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@maxlube.it', 'MaxlubeAdmin2024!')
    print('Superuser created')
else:
    print('Superuser already exists')
END

# Import products from CSV
python manage.py import_products --csv "data/Categorie prodotti Maxlube - Database.csv"