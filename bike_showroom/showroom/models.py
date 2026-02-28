from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Bike(models.Model):
    BIKE_TYPE_CHOICES = [
        ('sport', 'Sport'),
        ('cruiser', 'Cruiser'),
        ('adventure', 'Adventure'),
        ('naked', 'Naked/Street'),
        ('scooter', 'Scooter'),
        ('electric', 'Electric'),
        ('dirt', 'Dirt/Off-Road'),
        ('touring', 'Touring'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
        ('service', 'In Service'),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='bikes')
    model_name = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    bike_type = models.CharField(max_length=20, choices=BIKE_TYPE_CHOICES)
    engine_cc = models.PositiveIntegerField(verbose_name='Engine (CC)')
    color = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Mileage (kmpl)', blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='bikes/', blank=True, null=True)
    description = models.TextField(blank=True)
    vin_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand.name} {self.model_name} ({self.year})"

    class Meta:
        ordering = ['-created_at']


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    aadhar_number = models.CharField(max_length=20, blank=True, verbose_name='Aadhar Number')
    driving_license = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-created_at']


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('loan', 'Bank Loan'),
        ('emi', 'EMI'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='purchases')
    salesperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    sale_date = models.DateField(default=timezone.now)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def final_amount(self):
        return self.selling_price - self.discount

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Sale.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{timezone.now().year}-{num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.invoice_number} - {self.bike}"

    class Meta:
        ordering = ['-created_at']


class ServiceRecord(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('regular', 'Regular Service'),
        ('repair', 'Repair'),
        ('warranty', 'Warranty Claim'),
        ('inspection', 'Inspection'),
        ('tire', 'Tire Change'),
        ('battery', 'Battery Replacement'),
        ('oil', 'Oil Change'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='service_records')
    bike = models.ForeignKey(Bike, on_delete=models.SET_NULL, null=True, blank=True)
    bike_model = models.CharField(max_length=200, help_text="If bike not in inventory, enter manually")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    service_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField(blank=True, null=True)
    mechanic_notes = models.TextField(blank=True)
    customer_complaint = models.TextField(blank=True)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    km_reading = models.PositiveIntegerField(verbose_name='KM Reading', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.parts_cost + self.labor_cost

    def __str__(self):
        return f"Service - {self.customer} - {self.bike_model} ({self.service_date})"

    class Meta:
        ordering = ['-created_at']


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('interested', 'Interested'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    bike_interested = models.ForeignKey(Bike, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    follow_up_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Inquiry from {self.name} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('salesperson', 'Salesperson'),
        ('mechanic', 'Mechanic'),
        ('receptionist', 'Receptionist'),
        ('accountant', 'Accountant'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    join_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"
