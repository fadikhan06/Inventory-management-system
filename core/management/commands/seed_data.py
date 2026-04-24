"""
Management command to seed initial / demo data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import Shop, Category, Product
from accounts.models import UserProfile
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed initial demo data: shops, admin user, categories, and sample products.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding.')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Shop.objects.all().delete()

        # Create shop
        shop, created = Shop.objects.get_or_create(
            name='Main Shop',
            defaults={'address': '123 Main Street', 'phone': '+1-555-0100', 'email': 'main@shop.com'},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created shop: {shop.name}'))

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@shop.com', 'admin123')
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            admin.save()
            UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, shop=shop)
            self.stdout.write(self.style.SUCCESS('Created admin user (admin / admin123)'))

        # Create staff user
        if not User.objects.filter(username='staff').exists():
            staff_user = User.objects.create_user('staff', 'staff@shop.com', 'staff123')
            staff_user.first_name = 'Staff'
            staff_user.last_name = 'Member'
            staff_user.save()
            UserProfile.objects.create(user=staff_user, role=UserProfile.ROLE_STAFF, shop=shop)
            self.stdout.write(self.style.SUCCESS('Created staff user (staff / staff123)'))

        # Create categories
        categories_data = [
            ('Electronics', 'Electronic devices and accessories'),
            ('Clothing', 'Apparel and fashion items'),
            ('Food & Beverages', 'Grocery and drink items'),
            ('Stationery', 'Office and school supplies'),
            ('Home & Garden', 'Home improvement and garden items'),
        ]
        categories = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, shop=shop, defaults={'description': desc})
            categories[name] = cat

        # Create products
        products_data = [
            ('Smartphone X1', 'PHON-001', '1234567890', categories['Electronics'], Decimal('350.00'), Decimal('499.99'), 50, 10),
            ('Wireless Earbuds', 'EARBUD-001', '2345678901', categories['Electronics'], Decimal('25.00'), Decimal('49.99'), 100, 20),
            ('USB-C Cable', 'CABLE-001', '3456789012', categories['Electronics'], Decimal('3.00'), Decimal('9.99'), 200, 30),
            ('T-Shirt Basic', 'TSH-001', '4567890123', categories['Clothing'], Decimal('5.00'), Decimal('19.99'), 150, 20),
            ('Denim Jeans', 'JEAN-001', '5678901234', categories['Clothing'], Decimal('18.00'), Decimal('59.99'), 80, 15),
            ('Water Bottle', 'WBOT-001', '6789012345', categories['Food & Beverages'], Decimal('1.50'), Decimal('4.99'), 300, 50),
            ('Notebook A4', 'NOTE-001', '7890123456', categories['Stationery'], Decimal('1.00'), Decimal('3.99'), 500, 100),
            ('Ballpoint Pens (10pk)', 'PEN-001', '8901234567', categories['Stationery'], Decimal('1.20'), Decimal('4.99'), 400, 80),
            ('Plant Pot (Medium)', 'POT-001', '9012345678', categories['Home & Garden'], Decimal('3.00'), Decimal('9.99'), 60, 10),
            ('LED Bulb 9W', 'BULB-001', '0123456789', categories['Home & Garden'], Decimal('2.00'), Decimal('7.99'), 200, 30),
        ]
        for name, sku, barcode, cat, cost, price, qty, threshold in products_data:
            Product.objects.get_or_create(
                sku=sku, shop=shop,
                defaults={
                    'name': name, 'barcode': barcode, 'category': cat,
                    'cost_price': cost, 'selling_price': price,
                    'stock_qty': qty, 'low_stock_threshold': threshold,
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(products_data)} products.'))
        self.stdout.write(self.style.SUCCESS('Seed complete!'))
