from django.contrib import admin
from .models import Brand, Bike, Customer, Sale, ServiceRecord, Inquiry, StaffProfile


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'created_at']
    search_fields = ['name', 'country']


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ['brand', 'model_name', 'year', 'bike_type', 'price', 'status', 'stock_quantity']
    list_filter = ['status', 'bike_type', 'brand']
    search_fields = ['model_name', 'brand__name', 'vin_number']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'city', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'bike', 'customer', 'selling_price', 'payment_method', 'status', 'sale_date']
    list_filter = ['status', 'payment_method']
    search_fields = ['invoice_number', 'customer__first_name']


@admin.register(ServiceRecord)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'bike_model', 'service_type', 'status', 'service_date', 'total_cost']
    list_filter = ['status', 'service_type']


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'bike_interested', 'status', 'created_at']
    list_filter = ['status']


@admin.register(StaffProfile)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'is_active', 'join_date']
    list_filter = ['role', 'is_active']
