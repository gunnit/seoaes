#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

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