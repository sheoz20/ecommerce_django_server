"""
Django management command to seed the database with sample data.
Run with: python manage.py seed_data
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Seeding database with sample data...'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        # Create users
        self.stdout.write('\nCreating users...')
        self.create_admin_user()
        self.create_customer_user()
        
        # Create categories
        self.stdout.write('\nCreating categories...')
        categories = self.create_categories()
        
        # Create products
        self.stdout.write('\nCreating products...')
        self.create_products(categories)
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
        self.stdout.write('=' * 50)
        self.stdout.write('\nAdmin Login:')
        self.stdout.write('  Email: admin@example.com')
        self.stdout.write('  Password: admin123')
        self.stdout.write('\nCustomer Login:')
        self.stdout.write('  Email: customer@example.com')
        self.stdout.write('  Password: customer123')
        self.stdout.write('\nAPI Documentation:')
        self.stdout.write('  http://localhost:8000/api/docs/')

    def create_admin_user(self):
        """Create admin user."""
        admin, created = CustomUser.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': CustomUser.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin@example.com / admin123'))
        else:
            self.stdout.write('Admin user already exists')
        return admin

    def create_customer_user(self):
        """Create sample customer user."""
        customer, created = CustomUser.objects.get_or_create(
            email='customer@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'role': CustomUser.Role.CUSTOMER,
                'is_active': True,
            }
        )
        if created:
            customer.set_password('customer123')
            customer.save()
            self.stdout.write(self.style.SUCCESS('Created customer user: customer@example.com / customer123'))
        else:
            self.stdout.write('Customer user already exists')
        return customer

    def create_categories(self):
        """Create sample categories."""
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and accessories',
                'children': [
                    {'name': 'Smartphones', 'description': 'Mobile phones and accessories'},
                    {'name': 'Laptops', 'description': 'Notebooks and laptops'},
                    {'name': 'Accessories', 'description': 'Electronic accessories'},
                ]
            },
            {
                'name': 'Clothing',
                'description': 'Fashion and apparel',
                'children': [
                    {'name': 'Men', 'description': 'Men\'s clothing'},
                    {'name': 'Women', 'description': 'Women\'s clothing'},
                    {'name': 'Kids', 'description': 'Children\'s clothing'},
                ]
            },
            {
                'name': 'Home & Garden',
                'description': 'Home decor and garden supplies',
                'children': [
                    {'name': 'Furniture', 'description': 'Home furniture'},
                    {'name': 'Decor', 'description': 'Home decoration'},
                    {'name': 'Garden', 'description': 'Garden supplies'},
                ]
            },
            {
                'name': 'Sports',
                'description': 'Sports equipment and accessories',
                'children': [
                    {'name': 'Fitness', 'description': 'Fitness equipment'},
                    {'name': 'Outdoor', 'description': 'Outdoor sports'},
                ]
            },
        ]

        created_categories = []
        
        for cat_data in categories_data:
            children = cat_data.pop('children', [])
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
                created_categories.append(category)
            
            for child_data in children:
                child, created = Category.objects.get_or_create(
                    name=child_data['name'],
                    defaults={**child_data, 'parent': category}
                )
                if created:
                    self.stdout.write(f'  Created subcategory: {child.name}')
                    created_categories.append(child)
        
        return created_categories

    def create_products(self, categories):
        """Create sample products."""
        electronics = Category.objects.filter(name='Electronics').first()
        smartphones = Category.objects.filter(name='Smartphones').first()
        laptops = Category.objects.filter(name='Laptops').first()
        clothing = Category.objects.filter(name='Clothing').first()
        
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'description': 'The latest iPhone with advanced camera system and A17 Pro chip.',
                'short_description': 'Latest iPhone with pro camera system',
                'price': Decimal('999.00'),
                'compare_at_price': Decimal('1099.00'),
                'stock_quantity': 50,
                'category': smartphones or electronics,
                'tags': 'smartphone, apple, iphone, mobile',
                'status': 'active',
                'is_featured': True,
            },
            {
                'name': 'Samsung Galaxy S24',
                'description': 'Samsung\'s flagship smartphone with AI features.',
                'short_description': 'Samsung flagship with AI',
                'price': Decimal('899.00'),
                'stock_quantity': 40,
                'category': smartphones or electronics,
                'tags': 'smartphone, samsung, android, mobile',
                'status': 'active',
                'is_featured': True,
            },
            {
                'name': 'MacBook Pro 16"',
                'description': 'Apple\'s most powerful laptop with M3 Max chip.',
                'short_description': 'Powerful laptop with M3 Max',
                'price': Decimal('2499.00'),
                'stock_quantity': 25,
                'category': laptops or electronics,
                'tags': 'laptop, apple, macbook, computer',
                'status': 'active',
                'is_featured': True,
            },
            {
                'name': 'Dell XPS 15',
                'description': 'Premium Windows laptop with stunning display.',
                'short_description': 'Premium Windows laptop',
                'price': Decimal('1799.00'),
                'compare_at_price': Decimal('1999.00'),
                'stock_quantity': 30,
                'category': laptops or electronics,
                'tags': 'laptop, dell, windows, computer',
                'status': 'active',
            },
            {
                'name': 'Wireless Earbuds Pro',
                'description': 'Premium wireless earbuds with noise cancellation.',
                'short_description': 'Wireless earbuds with ANC',
                'price': Decimal('249.00'),
                'stock_quantity': 100,
                'category': electronics,
                'tags': 'audio, earbuds, wireless, headphones',
                'status': 'active',
            },
            {
                'name': 'Cotton T-Shirt',
                'description': 'Comfortable 100% cotton t-shirt in various colors.',
                'short_description': 'Comfortable cotton tee',
                'price': Decimal('29.99'),
                'stock_quantity': 200,
                'category': clothing,
                'tags': 'clothing, tshirt, cotton, casual',
                'status': 'active',
            },
            {
                'name': 'Running Shoes',
                'description': 'Lightweight running shoes with cushioned sole.',
                'short_description': 'Lightweight running shoes',
                'price': Decimal('129.99'),
                'stock_quantity': 75,
                'category': clothing,
                'tags': 'shoes, running, sports, footwear',
                'status': 'active',
                'is_featured': True,
            },
            {
                'name': 'Smart Watch',
                'description': 'Fitness tracking smartwatch with health monitoring.',
                'short_description': 'Fitness smartwatch',
                'price': Decimal('399.00'),
                'stock_quantity': 60,
                'category': electronics,
                'tags': 'smartwatch, fitness, wearable, tech',
                'status': 'active',
            },
            {
                'name': 'Bluetooth Speaker',
                'description': 'Portable Bluetooth speaker with 360-degree sound.',
                'short_description': 'Portable Bluetooth speaker',
                'price': Decimal('149.00'),
                'stock_quantity': 80,
                'category': electronics,
                'tags': 'audio, speaker, bluetooth, portable',
                'status': 'active',
            },
            {
                'name': 'Gaming Laptop',
                'description': 'High-performance gaming laptop with RTX graphics.',
                'short_description': 'Gaming laptop with RTX',
                'price': Decimal('1899.00'),
                'stock_quantity': 15,
                'category': laptops or electronics,
                'tags': 'laptop, gaming, computer, rtx',
                'status': 'active',
                'is_featured': True,
            },
        ]

        created_products = []
        
        for prod_data in products_data:
            category = prod_data.pop('category')
            if not category:
                continue
                
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={**prod_data, 'category': category}
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
                created_products.append(product)
        
        return created_products
