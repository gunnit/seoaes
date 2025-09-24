#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input

# Test database connection first
echo "Testing database connection..."
python manage.py test_db || echo "Warning: Database connection test failed"

# Try to run migrations with better error handling
echo "Running database migrations..."
python manage.py migrate --no-input || {
    echo "Warning: Migration failed, but continuing deployment..."
    echo "The application will start but database may need manual setup."
}

# Compile translation files (skip if .po files don't exist or are corrupt)
echo "Checking for translation files..."
if [ -f "locale/it/LC_MESSAGES/django.po" ] && [ -f "locale/en/LC_MESSAGES/django.po" ]; then
    echo "Compiling translation messages..."
    python manage.py compilemessages --ignore=venv || echo "Warning: Could not compile messages, continuing..."
else
    echo "Translation files not found, skipping compilation..."
fi

# Create superuser if it doesn't exist (skip if database not available)
echo "Checking for superuser..."
python manage.py shell << END || echo "Warning: Could not create superuser, database may not be ready"
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@maxlube.it', 'MaxlubeAdmin2024!')
        print('Superuser created')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Could not create superuser: {e}')
    exit(1)
END

# Import products from CSV (skip if file doesn't exist)
if [ -f "data/Categorie prodotti Maxlube - Database.csv" ]; then
    echo "Importing products from CSV..."
    python manage.py import_products --csv "data/Categorie prodotti Maxlube - Database.csv" || echo "Warning: Could not import products"
else
    echo "Product CSV file not found, skipping import..."
fi