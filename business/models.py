from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.conf import settings
import os
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal


 
def business_upload_path(instance, filename):
    return f"business/{instance.business_id}/{filename}"


def product_media_upload_path(instance, filename):
    return f"products/{instance.product.product_id}/{filename}"


class Category(models.Model):
    CATEGORY_LEVELS = (
        ('global', 'Global'),
        ('business', 'Business'),
        ('product', 'Product'),
    )

    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=20, choices=CATEGORY_LEVELS)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    display_order = models.PositiveIntegerField(null=True, blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.level})"





class Offer(models.Model):

    OFFER_TYPES = (
        ('discount_percent', 'Discount Percentage'),
        ('discount_flat', 'Flat Discount'),
        ('buy_x_get_y', 'Buy X Get Y'),
        ('free_gift', 'Free Gift'),
    )

    offer_type = models.CharField(max_length=30, choices=OFFER_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    x_quantity = models.PositiveIntegerField(null=True, blank=True)
    y_quantity = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)


    user = models.ForeignKey(
        "users.User",     # ✅ STRING
        on_delete=models.CASCADE,
        related_name="offers"
    )

    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        self.is_active = self.start_date <= today <= self.end_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.offer_type} - {self.description}"


class Business(models.Model):

    BUSINESS_TYPES = (
        ('individual', 'Individual'),
        ('proprietor', 'Proprietor'),
        ('partnership', 'Partnership'),
        ('private_limited', 'Private Limited'),
        ('llp', 'LLP'),
    )

    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    business_id = models.AutoField(primary_key=True)


    user = models.ForeignKey(
        "users.User",     # ✅ STRING
        on_delete=models.CASCADE,
        related_name="businesses"
    )

    business_name = models.CharField(max_length=255, unique=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=30, choices=BUSINESS_TYPES)
    #slug = models.SlugField(unique=True)
    slug = models.SlugField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Seller allowed categories
    categories = models.ManyToManyField(
        Category,
        limit_choices_to={'level': 'business'},
        related_name='businesses',
        blank=True
    )
    offer = models.ForeignKey(
        "business.Offer",     # ✅ STRING
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Branding
    logo = models.ImageField(upload_to=business_upload_path, blank=True, null=True)
    banner = models.ImageField(upload_to=business_upload_path, blank=True, null=True)

    # Contact
    support_email = models.EmailField()
    support_phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)

    # Address
    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10)

    # Compliance
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    gst_certificate = models.FileField(upload_to=business_upload_path, blank=True, null=True)
    pan_document = models.FileField(upload_to=business_upload_path, blank=True, null=True)

    # Bank
    bank_account_name = models.CharField(max_length=255)
    bank_account_number = models.CharField(max_length=50)
    bank_ifsc = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)

    # Marketplace rules
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    settlement_cycle_days = models.PositiveIntegerField(default=7)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Metrics
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_count = models.PositiveIntegerField(default=0)

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    rejection_reason = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name



class BusinessWorkingHour(models.Model):
    DAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    business = models.ForeignKey(
        Business,
        related_name='working_hours',
        on_delete=models.CASCADE
    )
    day = models.CharField(max_length=20, choices=DAYS)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('business', 'day')



class Product(models.Model):

    

    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    business = models.ForeignKey(
        "business.Business",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="products"
    )
    product_id = models.AutoField(primary_key=True)

    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    model_no = models.CharField(max_length=100, blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        limit_choices_to={'level': 'product'},
        blank=True,
        null=True
    )

    attributes = models.JSONField(blank=True, null=True)
    has_variants = models.BooleanField(default=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    rejection_reason = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    view_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def clean(self):
        category_id = getattr(self.category, 'pk', None)
        if category_id and not self.business.categories.filter(pk=category_id).exists():
            raise ValidationError("Business is not allowed to sell in this category.")


    @property
    def is_visible(self):
        return self.is_active and self.verification_status == 'verified'

    def __str__(self):
        return self.product_name


class ProductVariant(models.Model):

    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    product = models.ForeignKey(
        "business.Product",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="variants"
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )

    sku = models.CharField(max_length=100, unique=True)
    attributes = models.JSONField()

    mrp = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    cgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    sgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    stock = models.PositiveIntegerField(default=0)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)

    is_returnable = models.BooleanField(default=True)
    return_days = models.PositiveIntegerField(default=7)

    weight_kg = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    length_cm = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    width_cm = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    height_cm = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    company_commission = models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True,default=0.00)
    distribution_commission = models.DecimalField(max_digits=15, decimal_places=2,blank=True,null=True,default=0.00)

    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    
    offer = models.ForeignKey(
        "business.Offer",     # ✅ STRING
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    def apply_offer(self):
        if not self.offer or not self.offer.is_active:
            return self.mrp or Decimal('0')

        price = self.mrp or Decimal('0')

        if self.offer.offer_type == "discount_percent" and self.offer.value:
            return price - (price * Decimal(self.offer.value) / Decimal('100'))

        if self.offer.offer_type == "discount_flat" and self.offer.value:
            return max(price - Decimal(self.offer.value), Decimal('0'))

        if self.offer.offer_type == "buy_x_get_y" and self.offer.x_quantity and self.offer.y_quantity:
            free_ratio = Decimal(self.offer.y_quantity) / Decimal(self.offer.x_quantity)
            return price - (price * free_ratio)

        if self.offer.offer_type == "free_gift":
            return price

        return price


    def save(self, *args, **kwargs):
        # normalize decimals
        mrp = Decimal(str(self.mrp)) if self.mrp is not None else Decimal('0')
        sp = Decimal(str(self.selling_price)) if self.selling_price is not None else None
        price = sp or mrp

        cgst = Decimal(str(self.cgst_percent)) if self.cgst_percent is not None else Decimal('0')
        sgst = Decimal(str(self.sgst_percent)) if self.sgst_percent is not None else Decimal('0')

        # apply offer before tax
        self.selling_price = self.apply_offer()

        # tax calculations
        self.cgst_amount = (price * cgst / Decimal('100'))
        self.sgst_amount = (price * sgst / Decimal('100'))

        # auto deactivate if product not approved
        if self.product.verification_status != 'approved':
            self.is_active = False

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.product.product_name} - {self.attributes}"


class ProductMedia(models.Model):

    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    product = models.ForeignKey(
        "business.Product",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="media"
    )

    variant = models.ForeignKey(
        "business.ProductVariant",   # ✅ STRING
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media"
    )

    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to=product_media_upload_path)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductMedia.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


