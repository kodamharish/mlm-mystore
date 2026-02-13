from django.db import models
from users.models import *
from property.models import *
from subscription.models import *
from business.models import *


class Order(models.Model):
    # ORDER_STATUS_CHOICES = (
    #     ('pending', 'Pending'),
    #     ('paid', 'Paid'),
    #     ('cancelled', 'Cancelled'),
    #     ('refunded', 'Refunded'),
    # )
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    order_id = models.AutoField(primary_key=True)

    
    user = models.ForeignKey(
        "users.User",                     # ✅ STRING
        on_delete=models.CASCADE,
        related_name="orders"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.user}"




class OrderItem(models.Model):
    order = models.ForeignKey(
        "transactions.Order",
        on_delete=models.CASCADE,
        related_name="items"
    )

    variant = models.ForeignKey(
        "business.ProductVariant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="order_items"
    )

    property_item = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price snapshot at order time"
    )

    def get_subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        if self.variant:
            return f"{self.variant.sku} x {self.quantity}"
        return f"Property #{self.property_item.property_id}"



TRANSACTION_FOR_CHOICES = (
    ('property', 'Property'),
    ('subscription', 'Subscription'),
    ('product', 'Product'),
)

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    
    user_id = models.ForeignKey(
        "users.User",                     # ✅ STRING
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    property_id = models.ForeignKey(
        "property.Property",              # ✅ STRING
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transactions"
    )

    subscription_variant = models.ForeignKey(
        "subscription.SubscriptionPlanVariant",   # ✅ STRING
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    order = models.ForeignKey(
        "transactions.Order",                   # ✅ STRING
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transactions"
    )
    transaction_for = models.CharField(max_length=50, choices=TRANSACTION_FOR_CHOICES)  # NEW FIELD
    payment_type = models.CharField(max_length=100, blank=True, null=True)  # e.g., 'booking-amount', 'full-amount'
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    purchased_from = models.CharField(max_length=150, blank=True, null=True)
    purchased_type = models.CharField(max_length=150, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    # username = models.CharField(max_length=150,blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    receiver_upi_id = models.CharField(max_length=100, blank=True, null=True)
    plan_name = models.CharField(max_length=150, blank=True, null=True)
    
    property_name = models.CharField(max_length=150, blank=True, null=True)
    property_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    company_commission = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    document_type = models.CharField(max_length=20, choices=[('invoice', 'Invoice'), ('receipt', 'Receipt')], blank=True, null=True)
    document_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    document_file = models.FileField(upload_to='transaction_documents/', blank=True, null=True)
    phone_pe_merchant_order_id = models.CharField(max_length=200, blank=True, null=True)
    phone_pe_order_id = models.CharField(max_length=200, blank=True, null=True)
    phone_pe_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} -  ({self.transaction_for}, {self.payment_type})"


class UserProperty(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('purchased', 'Purchased'),
    )

    
    user = models.ForeignKey(
        "users.User",                     # ✅ STRING
        on_delete=models.CASCADE
    )

    property = models.ForeignKey(
        "property.Property",              # ✅ STRING
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    booking_date = models.DateField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')  # prevent duplicate booking/purchase by same user

    def __str__(self):
        return f"{self.user.first_name} - {self.property.property_title} ({self.status})"





class OrderAddress(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ("shipping", "Shipping"),
        ("billing", "Billing"),
    )

    order = models.ForeignKey(
        "transactions.Order",
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)

    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.address_type.title()} - Order #{self.order.order_id}"