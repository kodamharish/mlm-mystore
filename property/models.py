from django.db import models
#from users.models import *
from decimal import Decimal
import os
from dateutil.relativedelta import relativedelta
from datetime import timedelta, date


class PropertyCategory(models.Model):
    property_category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name


class PropertyType(models.Model):
    property_type_id = models.AutoField(primary_key=True)
    #category = models.ForeignKey(PropertyCategory, on_delete=models.CASCADE, related_name='types')
    category = models.ForeignKey(
        "property.PropertyCategory",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="types"
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Amenity(models.Model):
    amenity_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    


class BookingAmountSlab(models.Model):
    min_value = models.DecimalField(max_digits=15, decimal_places=2)
    max_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # null means "above"
    booking_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.max_value:
            return f"{self.min_value} - {self.max_value}: ₹{self.booking_amount}"
        else:
            return f"{self.min_value}+ : ₹{self.booking_amount}"



class Property(models.Model):
    LOOKING_TO_CHOICES = [
        ('sell', 'Sell'),
        # ('rent', 'Rent / Lease'),
        ('rent', 'Rent'),
        # ('pg', 'PG'),
    ]

    FACING_CHOICES = [
        ('east', 'East'),
        ('west', 'West'),
        ('north', 'North'),
        ('south', 'South'),
        ('north_east', 'North-East'),
        ('north_west', 'North-West'),
        ('south_east', 'South-East'),
        ('south_west', 'South-West'),
    ]
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    STATUS_CHOICES = (
        ('available','Available'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
    )

    property_id = models.AutoField(primary_key=True)
    # Basic Info
    looking_to = models.CharField(max_length=10, choices=LOOKING_TO_CHOICES,blank=True,null=True)
    #category = models.ForeignKey('PropertyCategory', on_delete=models.SET_NULL, null=True)
    #property_type = models.ForeignKey('PropertyType', on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(
        "property.PropertyCategory",   # ✅ STRING
        on_delete=models.SET_NULL,
        null=True
    )

    property_type = models.ForeignKey(
        "property.PropertyType",       # ✅ STRING
        on_delete=models.SET_NULL,
        null=True
    )
    property_title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    # Location Details
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    pin_code = models.CharField(max_length=15,blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    # Area and Dimensions
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    area_unit = models.CharField(max_length=100,blank=True, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    builtup_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    length_ft = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    breadth_ft = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    # Property Structure
    number_of_floors = models.PositiveIntegerField(blank=True, null=True)
    floor = models.PositiveIntegerField(blank=True, null=True)
    furnishing_status = models.CharField(max_length=100,blank=True, null=True)
    number_of_open_sides = models.PositiveIntegerField(blank=True, null=True)
    number_of_roads = models.PositiveIntegerField(blank=True, null=True)
    number_of_bedrooms = models.PositiveIntegerField(blank=True, null=True)
    number_of_balconies = models.PositiveIntegerField(blank=True, null=True)
    number_of_bathrooms = models.PositiveIntegerField(blank=True, null=True)
    road_width_1_ft = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    road_width_2_ft = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    # Facing
    facing = models.CharField(max_length=20, choices=FACING_CHOICES, blank=True, null=True)
    # Ownership & Financials
    ownership_type = models.CharField(max_length=100, blank=True, null=True)
    property_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0.00)
    total_property_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0.00)
    booking_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0.00)
    property_value_without_booking_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0.00)

    # Rent/Lease Specific Fields
    preferred_tenants = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Family, Bachelors, Company Lease")
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, default=0.00)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, default=0.00)
    # available_from = models.DateField(blank=True, null=True)
    available_from = models.CharField(max_length=100, blank=True, null=True)

    # Amenities
    #amenities = models.ManyToManyField(Amenity, blank=True,null=True)
    amenities = models.ManyToManyField(
        "property.Amenity",            # ✅ STRING
        blank=True
    )
    # Additional Info
    property_uniqueness = models.TextField(blank=True, null=True)
    location_advantages = models.TextField(blank=True, null=True)
    other_features = models.TextField(blank=True, null=True)
    listing_days = models.PositiveIntegerField(blank=True, null=True, help_text="Number of days the property stays visible")
    expiry_date = models.DateField(blank=True, null=True)
    # Owner Details
    owner_name = models.CharField(max_length=150, blank=True, null=True)
    owner_contact = models.CharField(max_length=15, blank=True, null=True)
    owner_email = models.EmailField(blank=True, null=True)
    # User
    # Who originally added the property
    #user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties_added')
    #added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_added_properties",null=True)
    user_id = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="properties_added"
    )

    added_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="user_added_properties",
        null=True
    )
    # Current owner of the property
    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_properties",null=True)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="owned_properties",
        null=True
    )
    role = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    referral_id = models.CharField(max_length=200, blank=True, null=True)
    agent_commission = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0.00)
    agent_commission_paid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True,default=0.00)
    agent_commission_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True,default=0.00)
    company_commission = models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True,default=0.00)
    distribution_commission = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    remaining_company_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_company_commission_distributed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    company_commission_status = models.CharField(max_length=100,default="unpaid")

    # Agreement (Single file & video)
    agreement_video = models.FileField(upload_to='agreements/videos/', null=True, blank=True)
    agreement_file = models.FileField(upload_to='agreements/files/', null=True, blank=True)
    # Flags
    is_featured = models.BooleanField(default=False)
    #status = models.CharField(max_length=100,default="available")
    #  Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    approval_status = models.CharField(max_length=100,default="pending")
    # Verification Status
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    view_count = models.PositiveIntegerField(default=0)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        # Step 1: Automatically calculate total property value
        self.total_property_value = (
            Decimal(self.agent_commission or 0) +
            Decimal(self.company_commission or 0) +
            Decimal(self.property_value or 0)
        )

        # Step 2: Get the booking amount slab that matches the total property value
        matching_slab = BookingAmountSlab.objects.filter(
            min_value__lte=self.total_property_value
        ).filter(
            models.Q(max_value__gte=self.total_property_value) | models.Q(max_value__isnull=True)
        ).order_by('min_value').first()

        # Step 3: Set the booking amount from the slab, or 0 if no slab is found
        if matching_slab:
            self.booking_amount = matching_slab.booking_amount
        else:
            self.booking_amount = Decimal(0)

        # ✅ Step 4: Now calculate property_value_without_booking_amount correctly
        self.property_value_without_booking_amount = (
            Decimal(self.total_property_value or 0) - Decimal(self.booking_amount or 0)
        )

        # -----------------------------
        # NEW: Auto-Generate Expiry Date
        # -----------------------------
        if self.listing_days:
            self.expiry_date = date.today() + timedelta(days=self.listing_days)

        # Step 5: Save the object
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.property_title or 'Untitled'} - {self.property_type.name if self.property_type else 'N/A'}"


    
def property_image_upload_to(instance, filename):
    user_id = instance.property.user_id.user_id
    return f'properties/{user_id}/images/{filename}'

def property_video_upload_to(instance, filename):
    # user_id = instance.property.user.id
    user_id = instance.property.user_id.user_id
    return f'properties/{user_id}/videos/{filename}'


def property_file_upload_to(instance, filename):
    # user_id = instance.property.user.id
    user_id = instance.property.user_id.user_id
    return f'properties/{user_id}/files/{filename}'


class PropertyImage(models.Model):
    #property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    property = models.ForeignKey(
        "property.Property",
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=property_image_upload_to)

    def __str__(self):
        return f"Image for {self.property}"


class PropertyVideo(models.Model):
    #property = models.ForeignKey(Property, related_name='videos', on_delete=models.CASCADE)
    property = models.ForeignKey(
        "property.Property",
        related_name="videos",
        on_delete=models.CASCADE
    )
    video = models.FileField(upload_to=property_video_upload_to)

    def __str__(self):
        return f"Video for {self.property}"


class PropertyFile(models.Model):
    #property = models.ForeignKey(Property, related_name='files', on_delete=models.CASCADE)
    property = models.ForeignKey(
        "property.Property",
        related_name="files",
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=property_file_upload_to)

    def __str__(self):
        return f"File for {self.property}"


class EMIOption(models.Model):
    #property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name="emi_options")
    property = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE,
        related_name="emi_options"
    )
    period_months = models.PositiveIntegerField()
    emi_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True)

    class Meta:
        unique_together = ('property', 'period_months')  # prevents duplicate period for same property

    
    def save(self, *args, **kwargs):
        if self.property and self.property.total_property_value and self.period_months:
            # Subtract booking amount from total value before EMI calculation
            loan_amount = self.property.total_property_value - (self.property.booking_amount or 0)
            self.emi_amount = loan_amount / Decimal(self.period_months)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.period_months} months - ₹{self.emi_amount:.2f}"



class UserEMI(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    #property = models.ForeignKey(Property, on_delete=models.CASCADE)
    #emi_option = models.ForeignKey(EMIOption, on_delete=models.CASCADE)
    user = models.ForeignKey(
        "users.User",   # ✅ STRING
        on_delete=models.CASCADE
    )
    property = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE
    )
    emi_option = models.ForeignKey(
        "property.EMIOption",
        on_delete=models.CASCADE
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.start_date and self.emi_option:
            self.end_date = self.start_date + relativedelta(months=self.emi_option.period_months)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.emi_option.period_months}M EMI for {self.property}"


class Notification(models.Model):
    message = models.CharField(max_length=255)
    #property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='notifications')
    property = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    #is_read = models.BooleanField(default=False)
    #visible_to_users = models.ManyToManyField(User, related_name='notifications_visible_to')
    visible_to_users = models.ManyToManyField(
        "users.User",   # ✅ STRING
        related_name="notifications_visible_to"
    )

    def __str__(self):
        return f"{self.message} - {self.property.property_title}"



class UserNotificationStatus(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    #notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE
    )
    notification = models.ForeignKey(
        "property.Notification",
        on_delete=models.CASCADE
    )
    is_read = models.BooleanField(default=False)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'notification')




class UserProperty(models.Model):
    # STATUS_CHOICES = [
    #     ('booked', 'Booked'),
    #     ('purchased', 'Purchased'),
    # ]
    # STATUS_CHOICES = [
    #     ('booked', 'Booked'),
    #     ('sold', 'Sold'),
    # ]

    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('purchased', 'Purchased'),
    )

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name='user_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='user_properties')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    booking_date = models.DateField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')  # prevent duplicate booking/purchase by same user

    def __str__(self):
        return f"{self.user.first_name} - {self.property.property_title} ({self.status})"



