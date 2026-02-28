from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Bike, Brand, Customer, Sale, ServiceRecord, Inquiry, StaffProfile
from .forms import (LoginForm, BikeForm, BrandForm, CustomerForm,
                    SaleForm, ServiceForm, InquiryForm, StaffForm)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name or user.username}!")
        return redirect('dashboard')
    return render(request, 'showroom/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    today = timezone.now().date()
    this_month = today.replace(day=1)

    total_bikes = Bike.objects.count()
    available_bikes = Bike.objects.filter(status='available').count()
    total_customers = Customer.objects.count()
    total_sales = Sale.objects.filter(status='completed').count()

    monthly_revenue = Sale.objects.filter(
        status='completed', sale_date__gte=this_month
    ).aggregate(total=Sum('selling_price'))['total'] or 0

    monthly_discount = Sale.objects.filter(
        status='completed', sale_date__gte=this_month
    ).aggregate(total=Sum('discount'))['total'] or 0
    monthly_revenue -= monthly_discount

    total_revenue = Sale.objects.filter(status='completed').aggregate(
        total=Sum('selling_price'))['total'] or 0

    pending_services = ServiceRecord.objects.filter(status__in=['pending', 'in_progress']).count()
    new_inquiries = Inquiry.objects.filter(status='new').count()

    recent_sales = Sale.objects.select_related('bike', 'customer').order_by('-created_at')[:5]
    recent_services = ServiceRecord.objects.select_related('customer').order_by('-created_at')[:5]
    recent_inquiries = Inquiry.objects.order_by('-created_at')[:5]

    # Monthly sales for chart (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=i * 30)
        month_start = d.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        count = Sale.objects.filter(
            status='completed',
            sale_date__gte=month_start,
            sale_date__lt=month_end
        ).count()
        monthly_data.append({'month': month_start.strftime('%b'), 'count': count})

    # Bike type distribution
    bike_types = Bike.objects.values('bike_type').annotate(count=Count('id'))

    context = {
        'total_bikes': total_bikes,
        'available_bikes': available_bikes,
        'total_customers': total_customers,
        'total_sales': total_sales,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'pending_services': pending_services,
        'new_inquiries': new_inquiries,
        'recent_sales': recent_sales,
        'recent_services': recent_services,
        'recent_inquiries': recent_inquiries,
        'monthly_data': monthly_data,
        'bike_types': list(bike_types),
    }
    return render(request, 'showroom/dashboard.html', context)


# ---- BIKES ----
@login_required
def bike_list(request):
    bikes = Bike.objects.select_related('brand').all()
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    bike_type = request.GET.get('type', '')

    if query:
        bikes = bikes.filter(
            Q(model_name__icontains=query) | Q(brand__name__icontains=query) | Q(color__icontains=query)
        )
    if status:
        bikes = bikes.filter(status=status)
    if bike_type:
        bikes = bikes.filter(bike_type=bike_type)

    context = {
        'bikes': bikes,
        'query': query,
        'status': status,
        'bike_type': bike_type,
        'status_choices': Bike.STATUS_CHOICES,
        'type_choices': Bike.BIKE_TYPE_CHOICES,
    }
    return render(request, 'showroom/bikes/list.html', context)


@login_required
def bike_detail(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    sales = Sale.objects.filter(bike=bike).order_by('-sale_date')
    return render(request, 'showroom/bikes/detail.html', {'bike': bike, 'sales': sales})


@login_required
def bike_add(request):
    form = BikeForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bike added successfully!')
        return redirect('bike_list')
    return render(request, 'showroom/bikes/form.html', {'form': form, 'title': 'Add Bike'})


@login_required
def bike_edit(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    form = BikeForm(request.POST or None, request.FILES or None, instance=bike)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bike updated successfully!')
        return redirect('bike_detail', pk=bike.pk)
    return render(request, 'showroom/bikes/form.html', {'form': form, 'title': 'Edit Bike', 'bike': bike})


@login_required
def bike_delete(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    if request.method == 'POST':
        bike.delete()
        messages.success(request, 'Bike deleted!')
        return redirect('bike_list')
    return render(request, 'showroom/confirm_delete.html', {'object': bike, 'type': 'Bike'})


# ---- BRANDS ----
@login_required
def brand_list(request):
    brands = Brand.objects.annotate(bike_count=Count('bikes'))
    return render(request, 'showroom/brands/list.html', {'brands': brands})


@login_required
def brand_add(request):
    form = BrandForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Brand added!')
        return redirect('brand_list')
    return render(request, 'showroom/brands/form.html', {'form': form, 'title': 'Add Brand'})


@login_required
def brand_edit(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    form = BrandForm(request.POST or None, request.FILES or None, instance=brand)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Brand updated!')
        return redirect('brand_list')
    return render(request, 'showroom/brands/form.html', {'form': form, 'title': 'Edit Brand', 'brand': brand})


@login_required
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.delete()
        messages.success(request, 'Brand deleted!')
        return redirect('brand_list')
    return render(request, 'showroom/confirm_delete.html', {'object': brand, 'type': 'Brand'})


# ---- CUSTOMERS ----
@login_required
def customer_list(request):
    customers = Customer.objects.all()
    query = request.GET.get('q', '')
    if query:
        customers = customers.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) |
            Q(email__icontains=query) | Q(phone__icontains=query)
        )
    return render(request, 'showroom/customers/list.html', {'customers': customers, 'query': query})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = Sale.objects.filter(customer=customer).select_related('bike')
    services = ServiceRecord.objects.filter(customer=customer)
    return render(request, 'showroom/customers/detail.html', {
        'customer': customer, 'sales': sales, 'services': services
    })


@login_required
def customer_add(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Customer added!')
        return redirect('customer_list')
    return render(request, 'showroom/customers/form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Customer updated!')
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'showroom/customers/form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted!')
        return redirect('customer_list')
    return render(request, 'showroom/confirm_delete.html', {'object': customer, 'type': 'Customer'})


# ---- SALES ----
@login_required
def sale_list(request):
    sales = Sale.objects.select_related('bike', 'customer', 'salesperson').all()
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if query:
        sales = sales.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__first_name__icontains=query) |
            Q(bike__model_name__icontains=query)
        )
    if status:
        sales = sales.filter(status=status)
    total_revenue = sales.filter(status='completed').aggregate(t=Sum('selling_price'))['t'] or 0
    return render(request, 'showroom/sales/list.html', {
        'sales': sales, 'query': query, 'status': status,
        'total_revenue': total_revenue, 'status_choices': Sale.STATUS_CHOICES
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'showroom/sales/detail.html', {'sale': sale})


@login_required
def sale_add(request):
    form = SaleForm(request.POST or None, initial={'salesperson': request.user})
    if request.method == 'POST' and form.is_valid():
        sale = form.save()
        # Update bike status if sold
        if sale.status == 'completed':
            bike = sale.bike
            if bike.stock_quantity > 0:
                bike.stock_quantity -= 1
            if bike.stock_quantity == 0:
                bike.status = 'sold'
            bike.save()
        messages.success(request, f'Sale recorded! Invoice: {sale.invoice_number}')
        return redirect('sale_detail', pk=sale.pk)
    return render(request, 'showroom/sales/form.html', {'form': form, 'title': 'New Sale'})


@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    form = SaleForm(request.POST or None, instance=sale)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sale updated!')
        return redirect('sale_detail', pk=sale.pk)
    return render(request, 'showroom/sales/form.html', {'form': form, 'title': 'Edit Sale', 'sale': sale})


@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted!')
        return redirect('sale_list')
    return render(request, 'showroom/confirm_delete.html', {'object': sale, 'type': 'Sale'})


# ---- SERVICE ----
@login_required
def service_list(request):
    services = ServiceRecord.objects.select_related('customer').all()
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if query:
        services = services.filter(
            Q(customer__first_name__icontains=query) |
            Q(bike_model__icontains=query)
        )
    if status:
        services = services.filter(status=status)
    return render(request, 'showroom/services/list.html', {
        'services': services, 'query': query, 'status': status,
        'status_choices': ServiceRecord.STATUS_CHOICES
    })


@login_required
def service_add(request):
    form = ServiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service record added!')
        return redirect('service_list')
    return render(request, 'showroom/services/form.html', {'form': form, 'title': 'New Service'})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(ServiceRecord, pk=pk)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service record updated!')
        return redirect('service_list')
    return render(request, 'showroom/services/form.html', {
        'form': form, 'title': 'Edit Service', 'service': service
    })


@login_required
def service_delete(request, pk):
    service = get_object_or_404(ServiceRecord, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service record deleted!')
        return redirect('service_list')
    return render(request, 'showroom/confirm_delete.html', {'object': service, 'type': 'Service Record'})


# ---- INQUIRIES ----
@login_required
def inquiry_list(request):
    inquiries = Inquiry.objects.select_related('bike_interested').all()
    status = request.GET.get('status', '')
    if status:
        inquiries = inquiries.filter(status=status)
    return render(request, 'showroom/inquiries/list.html', {
        'inquiries': inquiries, 'status': status,
        'status_choices': Inquiry.STATUS_CHOICES
    })


@login_required
def inquiry_add(request):
    form = InquiryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Inquiry added!')
        return redirect('inquiry_list')
    return render(request, 'showroom/inquiries/form.html', {'form': form, 'title': 'New Inquiry'})


@login_required
def inquiry_edit(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    form = InquiryForm(request.POST or None, instance=inquiry)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Inquiry updated!')
        return redirect('inquiry_list')
    return render(request, 'showroom/inquiries/form.html', {
        'form': form, 'title': 'Edit Inquiry', 'inquiry': inquiry
    })


@login_required
def inquiry_delete(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST':
        inquiry.delete()
        messages.success(request, 'Inquiry deleted!')
        return redirect('inquiry_list')
    return render(request, 'showroom/confirm_delete.html', {'object': inquiry, 'type': 'Inquiry'})


# ---- STAFF ----
@login_required
def staff_list(request):
    staff = StaffProfile.objects.select_related('user').all()
    return render(request, 'showroom/staff/list.html', {'staff': staff})


@login_required
def staff_add(request):
    form = StaffForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            password=form.cleaned_data['password'] or 'changeme123'
        )
        profile = form.save(commit=False)
        profile.user = user
        profile.save()
        messages.success(request, 'Staff member added!')
        return redirect('staff_list')
    return render(request, 'showroom/staff/form.html', {'form': form, 'title': 'Add Staff'})


@login_required
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    initial = {
        'first_name': profile.user.first_name,
        'last_name': profile.user.last_name,
        'email': profile.user.email,
        'username': profile.user.username,
    }
    form = StaffForm(request.POST or None, instance=profile, initial=initial)
    if request.method == 'POST' and form.is_valid():
        profile.user.first_name = form.cleaned_data['first_name']
        profile.user.last_name = form.cleaned_data['last_name']
        profile.user.email = form.cleaned_data['email']
        if form.cleaned_data['password']:
            profile.user.set_password(form.cleaned_data['password'])
        profile.user.save()
        form.save()
        messages.success(request, 'Staff updated!')
        return redirect('staff_list')
    return render(request, 'showroom/staff/form.html', {
        'form': form, 'title': 'Edit Staff', 'profile': profile
    })


@login_required
def staff_delete(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        profile.user.delete()
        messages.success(request, 'Staff deleted!')
        return redirect('staff_list')
    return render(request, 'showroom/confirm_delete.html', {'object': profile, 'type': 'Staff Member'})


# ---- REPORTS ----
@login_required
def reports(request):
    today = timezone.now().date()
    this_month = today.replace(day=1)
    this_year = today.replace(month=1, day=1)

    # Sales stats
    total_sales_revenue = Sale.objects.filter(status='completed').aggregate(
        revenue=Sum('selling_price'), discount=Sum('discount'))
    revenue = (total_sales_revenue['revenue'] or 0) - (total_sales_revenue['discount'] or 0)

    monthly_sales = Sale.objects.filter(status='completed', sale_date__gte=this_month)
    monthly_revenue = monthly_sales.aggregate(
        revenue=Sum('selling_price'), discount=Sum('discount'))
    m_rev = (monthly_revenue['revenue'] or 0) - (monthly_revenue['discount'] or 0)

    # Top selling bikes
    top_bikes = Sale.objects.filter(status='completed').values(
        'bike__brand__name', 'bike__model_name'
    ).annotate(count=Count('id')).order_by('-count')[:5]

    # Sales by payment method
    payment_stats = Sale.objects.filter(status='completed').values(
        'payment_method').annotate(count=Count('id'), total=Sum('selling_price'))

    # Service revenue
    service_revenue = ServiceRecord.objects.filter(status='completed').aggregate(
        parts=Sum('parts_cost'), labor=Sum('labor_cost'))

    context = {
        'total_revenue': revenue,
        'monthly_revenue': m_rev,
        'total_sales_count': Sale.objects.filter(status='completed').count(),
        'monthly_sales_count': monthly_sales.count(),
        'top_bikes': top_bikes,
        'payment_stats': payment_stats,
        'service_parts_revenue': service_revenue['parts'] or 0,
        'service_labor_revenue': service_revenue['labor'] or 0,
        'total_customers': Customer.objects.count(),
        'new_customers_month': Customer.objects.filter(created_at__date__gte=this_month).count(),
    }
    return render(request, 'showroom/reports.html', context)
