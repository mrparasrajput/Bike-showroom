from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from showroom.models import Brand, Bike, Customer, Sale, ServiceRecord, Inquiry, StaffProfile
from django.utils import timezone
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Set up demo data for BikeZone showroom'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        # Create superuser
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@bikezone.com', 'admin123')
            admin.first_name = 'Admin'
            admin.last_name = 'Manager'
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user (admin/admin123)'))

        # Create staff
        staff_data = [
            ('rahul', 'Rahul', 'Sharma', 'rahul@bikezone.com', 'salesperson'),
            ('priya', 'Priya', 'Patel', 'priya@bikezone.com', 'salesperson'),
            ('amit', 'Amit', 'Verma', 'amit@bikezone.com', 'mechanic'),
        ]
        for username, first, last, email, role in staff_data:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username, email, 'staff123', first_name=first, last_name=last)
                StaffProfile.objects.create(user=user, role=role, phone=f'9{random.randint(100000000,999999999)}',
                                             salary=Decimal(random.choice([25000, 30000, 35000])))

        # Create brands
        brands_data = [
            ('Royal Enfield', 'India'),
            ('Hero MotoCorp', 'India'),
            ('Honda', 'Japan'),
            ('Bajaj', 'India'),
            ('Yamaha', 'Japan'),
            ('KTM', 'Austria'),
            ('TVS', 'India'),
            ('Suzuki', 'Japan'),
        ]
        brands = {}
        for name, country in brands_data:
            brand, _ = Brand.objects.get_or_create(name=name, defaults={'country': country})
            brands[name] = brand

        # Create bikes
        bikes_data = [
            ('Royal Enfield', 'Classic 350', 2023, 'cruiser', 350, 'Gunmetal Grey', 185000, 35.0),
            ('Royal Enfield', 'Meteor 350', 2024, 'cruiser', 350, 'Fireball Orange', 210000, 36.2),
            ('Royal Enfield', 'Hunter 350', 2024, 'naked', 350, 'Dapper Ash', 175000, 36.5),
            ('Honda', 'CB350RS', 2023, 'naked', 350, 'Pearl Spartan Red', 215000, 45.0),
            ('Honda', 'CB Unicorn', 2024, 'naked', 160, 'Pearl Amazona Green', 95000, 60.5),
            ('Bajaj', 'Pulsar NS200', 2024, 'sport', 200, 'Burnt Red', 135000, 45.0),
            ('Bajaj', 'Dominar 400', 2023, 'adventure', 373, 'Aurora Green', 225000, 30.0),
            ('Yamaha', 'MT-15 V2', 2024, 'naked', 155, 'Metallic Black', 160000, 47.5),
            ('KTM', 'Duke 200', 2023, 'naked', 200, 'Orange', 190000, 40.0),
            ('KTM', 'Duke 390', 2024, 'naked', 373, 'Orange', 310000, 30.0),
            ('TVS', 'Apache RTR 160 4V', 2024, 'sport', 160, 'Red', 125000, 52.0),
            ('Suzuki', 'Gixxer 250', 2023, 'sport', 250, 'Metallic Sonic Silver', 195000, 42.0),
            ('Hero MotoCorp', 'Splendor Plus', 2024, 'scooter', 97, 'Black', 72000, 70.0),
            ('Bajaj', 'Avenger Street 160', 2023, 'cruiser', 160, 'Ebony Black', 115000, 45.0),
            ('Yamaha', 'FZ-S FI V4', 2024, 'naked', 150, 'Matte Cyan Storm', 115000, 50.0),
        ]

        created_bikes = []
        for brand_name, model, year, btype, engine, color, price, mileage in bikes_data:
            bike, _ = Bike.objects.get_or_create(
                brand=brands[brand_name], model_name=model,
                defaults={
                    'year': year, 'bike_type': btype, 'engine_cc': engine,
                    'color': color, 'price': Decimal(price), 'mileage': Decimal(mileage),
                    'stock_quantity': random.randint(1, 5),
                    'status': random.choice(['available', 'available', 'available', 'reserved']),
                }
            )
            created_bikes.append(bike)

        # Create customers
        customers_data = [
            ('Arjun', 'Singh', 'arjun@gmail.com', '9876543210', 'Mumbai', 'Maharashtra'),
            ('Sneha', 'Gupta', 'sneha@gmail.com', '9123456780', 'Pune', 'Maharashtra'),
            ('Vikram', 'Joshi', 'vikram@gmail.com', '9234567890', 'Nashik', 'Maharashtra'),
            ('Pooja', 'Nair', 'pooja@gmail.com', '9345678901', 'Mumbai', 'Maharashtra'),
            ('Ravi', 'Kumar', 'ravi@gmail.com', '9456789012', 'Thane', 'Maharashtra'),
            ('Ananya', 'Desai', 'ananya@gmail.com', '9567890123', 'Pune', 'Maharashtra'),
            ('Karan', 'Mehta', 'karan@gmail.com', '9678901234', 'Mumbai', 'Maharashtra'),
            ('Deepika', 'Shah', 'deepika@gmail.com', '9789012345', 'Navi Mumbai', 'Maharashtra'),
        ]

        created_customers = []
        for first, last, email, phone, city, state in customers_data:
            customer, _ = Customer.objects.get_or_create(
                email=email,
                defaults={'first_name': first, 'last_name': last, 'phone': phone,
                          'city': city, 'state': state}
            )
            created_customers.append(customer)

        # Create sales
        admin_user = User.objects.get(username='admin')
        payment_methods = ['cash', 'loan', 'emi', 'card', 'upi']

        if Sale.objects.count() < 5:
            for i in range(min(10, len(created_bikes), len(created_customers))):
                bike = created_bikes[i % len(created_bikes)]
                customer = created_customers[i % len(created_customers)]
                sale = Sale.objects.create(
                    bike=bike,
                    customer=customer,
                    salesperson=admin_user,
                    sale_date=timezone.now().date() - timezone.timedelta(days=random.randint(0, 60)),
                    selling_price=bike.price,
                    discount=Decimal(random.choice([0, 2000, 5000, 10000])),
                    payment_method=random.choice(payment_methods),
                    status='completed',
                )

        # Create service records
        if ServiceRecord.objects.count() < 3:
            service_types = ['regular', 'oil', 'tire', 'repair']
            for i in range(5):
                ServiceRecord.objects.create(
                    customer=created_customers[i % len(created_customers)],
                    bike_model=f"{created_bikes[i % len(created_bikes)].brand.name} {created_bikes[i % len(created_bikes)].model_name}",
                    service_type=random.choice(service_types),
                    status=random.choice(['pending', 'in_progress', 'completed']),
                    service_date=timezone.now().date() - timezone.timedelta(days=random.randint(0, 30)),
                    parts_cost=Decimal(random.randint(200, 3000)),
                    labor_cost=Decimal(random.randint(300, 2000)),
                    km_reading=random.randint(1000, 50000),
                    customer_complaint='Routine maintenance and service check',
                )

        # Create inquiries
        if Inquiry.objects.count() < 3:
            for i in range(5):
                Inquiry.objects.create(
                    name=f"{created_customers[i].first_name} {created_customers[i].last_name}",
                    phone=created_customers[i].phone,
                    email=created_customers[i].email,
                    bike_interested=created_bikes[i % len(created_bikes)],
                    status=random.choice(['new', 'contacted', 'interested']),
                    message='Interested in test ride and pricing details',
                )

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Demo data created successfully!'
            '\n📊 Login: admin / admin123'
            '\n🔗 Run: python manage.py runserver'
        ))
