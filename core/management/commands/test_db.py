from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import sys


class Command(BaseCommand):
    help = 'Test database connectivity'

    def handle(self, *args, **kwargs):
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))

                    # Try to check if tables exist
                    cursor.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                    """)
                    tables = cursor.fetchall()

                    if tables:
                        self.stdout.write(self.style.SUCCESS(f'✓ Found {len(tables)} tables in database'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠ No tables found - run migrations'))

        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Unexpected error: {e}'))
            sys.exit(1)