import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Product, Brand, MacroCategory, Category, SubCategory


class Command(BaseCommand):
    help = 'Import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='data/Categorie prodotti Maxlube - Database.csv',
            help='Path to CSV file'
        )

    def handle(self, *args, **options):
        csv_file = options['csv']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} does not exist'))
            return

        self.stdout.write(self.style.SUCCESS(f'Importing products from {csv_file}...'))

        # Track statistics
        stats = {
            'products': 0,
            'brands': 0,
            'macros': 0,
            'categories': 0,
            'subcategories': 0,
            'errors': 0
        }

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    # Get or create Brand
                    brand_name = row.get('Marchio', '').strip()
                    brand = None
                    if brand_name:
                        brand, created = Brand.objects.get_or_create(
                            name=brand_name,
                            defaults={'slug': slugify(brand_name)}
                        )
                        if created:
                            stats['brands'] += 1

                    # Get or create MacroCategory
                    macro_name = row.get('Macro (lubrificanti / ausiliari per industria)', '').strip()
                    macro = None
                    if macro_name:
                        macro, created = MacroCategory.objects.get_or_create(
                            name=macro_name,
                            defaults={
                                'slug': slugify(macro_name),
                                'description': f'Categoria principale: {macro_name}'
                            }
                        )
                        if created:
                            stats['macros'] += 1

                    # Get or create Category
                    category_name = row.get('Categoria / Categorie di appartenenza', '').strip()
                    category = None
                    if category_name and macro:
                        category_slug = slugify(category_name)
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            macro_category=macro,
                            defaults={
                                'slug': category_slug,
                                'description': f'Categoria: {category_name}'
                            }
                        )
                        if created:
                            stats['categories'] += 1

                    # Get or create SubCategory
                    subcategory_name = row.get('Sottocategoria / Sottocategorie di appartenenza', '').strip()
                    subcategory = None
                    if subcategory_name and category:
                        subcategory_slug = slugify(subcategory_name)
                        subcategory, created = SubCategory.objects.get_or_create(
                            name=subcategory_name,
                            category=category,
                            defaults={
                                'slug': subcategory_slug,
                                'description': f'Sottocategoria: {subcategory_name}'
                            }
                        )
                        if created:
                            stats['subcategories'] += 1

                    # Create or update Product
                    product_name = row.get('Nome prodotto', '').strip()
                    if not product_name:
                        continue

                    # Generate unique slug
                    base_slug = slugify(product_name)
                    slug = base_slug
                    counter = 1
                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    # Create product
                    product, created = Product.objects.update_or_create(
                        name=product_name,
                        defaults={
                            'slug': slug,
                            'brand': brand,
                            'macro_category': macro,
                            'category': category,
                            'subcategory': subcategory,
                            'description': row.get('Descrizione prodotto (facoltativa)', '').strip(),
                            'application': row.get('Applicazione', '').strip(),
                            'observation': row.get('Osservazione', '').strip(),
                            'notes': row.get('Note', '').strip(),
                            'is_active': True,
                            'in_stock': True,
                        }
                    )

                    if created:
                        stats['products'] += 1
                        self.stdout.write(f"  Created: {product_name}")
                    else:
                        self.stdout.write(f"  Updated: {product_name}")

                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error processing row: {row.get('Nome prodotto', 'Unknown')}: {str(e)}")
                    )

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n=== Import Summary ==='))
        self.stdout.write(f"Products created: {stats['products']}")
        self.stdout.write(f"Brands created: {stats['brands']}")
        self.stdout.write(f"Macro categories created: {stats['macros']}")
        self.stdout.write(f"Categories created: {stats['categories']}")
        self.stdout.write(f"Subcategories created: {stats['subcategories']}")
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"Errors: {stats['errors']}"))

        self.stdout.write(self.style.SUCCESS('\nImport completed!'))