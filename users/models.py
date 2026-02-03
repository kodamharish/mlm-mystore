from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.conf import settings
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
#from business.models import *


def temp_directory_path(instance, filename):
    """Save files temporarily in a 'temp' folder."""
    ext = filename.split('.')[-1]
    return f"temp/{filename.split('.')[0]}.{ext}"


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role_id}"




class User(models.Model):
    STATUS_CHOICES = (
        ('active','Active'),
        ('inactive', 'Inactive'),
        
    )
    MARITAL_STATUS = (
        ('single','Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        
    )
    Gender = (
        ('female','Female'),
        ('male', 'Male'),
        ('other', 'Other'),    
    )
    

    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    user_id = models.AutoField(primary_key=True)
    roles = models.ManyToManyField('Role')
    username = models.CharField(max_length=255,null=True, blank=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    pin_code = models.CharField(max_length=20, blank=True, null=True)
    #status = models.CharField(max_length=100, default='inactive')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive'
    )
    marital_status = models.CharField(max_length=50,choices=MARITAL_STATUS,blank=True, null=True)
    gender = models.CharField(max_length=20,choices=Gender,null=True, blank=True)

    pan_number = models.CharField(max_length=10, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)

    # === New upload fields ===
    aadhaar_front = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    aadhaar_back = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    nominee_aadhaar_front = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    nominee_aadhaar_back = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    pan_front = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    pan_back = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    bank_passbook = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    cancelled_cheque = models.ImageField(upload_to=temp_directory_path, blank=True, null=True)
    # ========================

    kyc_status = models.CharField(max_length=100,choices=VERIFICATION_STATUS,default='pending')
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    account_type = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=60, blank=True, null=True)
    nominee_reference_to = models.CharField(max_length=255, blank=True, null=True)
    nominee_relationship = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #referral_id = models.CharField(max_length=255,  blank=True, null=True)
    referral_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    referred_by = models.CharField(max_length=255, blank=True, null=True)
    level_no = models.PositiveIntegerField(default=0)

    def set_roles(self, roles):
        """Temporarily store roles to set after save."""
        self._roles_data = roles

    def save(self, *args, **kwargs):
        new_user = not self.pk
        # Set level_no based on referred_by
        if self.referred_by:
            try:
                referring_user = User.objects.get(referral_id=self.referred_by)
                self.level_no = (referring_user.level_no or 0) + 1
            except User.DoesNotExist:
                self.level_no = 0
        else:
            self.level_no = 0

        # Handle file cleanup if updating
        if self.pk:
            existing_user = User.objects.get(pk=self.pk)
            for file_field in [
                'image', 'aadhaar_front', 'aadhaar_back',
                'nominee_aadhaar_front','nominee_aadhaar_back',
                'pan_front', 'pan_back',
                'bank_passbook', 'cancelled_cheque'
            ]:
                new_file = getattr(self, file_field)
                old_file = getattr(existing_user, file_field)
                if new_file and old_file and old_file.name != new_file.name:
                    old_file_path = os.path.join(settings.MEDIA_ROOT, old_file.name)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

        # Hash password if not already hashed
        if self.pk:
            existing_user = User.objects.get(pk=self.pk)
            if self.password != existing_user.password and not self.password.startswith('pbkdf2_sha256$'):
                self.password = make_password(self.password)
        else:
            if not self.password.startswith('pbkdf2_sha256$'):
                self.password = make_password(self.password)

        super().save(*args, **kwargs)

        # Move files to user folder
        self.move_files_to_user_folder()

        # Assign roles if provided
        if hasattr(self, '_roles_data'):
            self.roles.set(self._roles_data)

    def move_files_to_user_folder(self):
        """Move files from temp folder to user_id folder after user creation."""
        for file_field in [
            'image', 'aadhaar_front', 'aadhaar_back','nominee_aadhaar_front','nominee_aadhaar_back',
            'pan_front', 'pan_back',
            'bank_passbook', 'cancelled_cheque'
        ]:
            file_instance = getattr(self, file_field)
            if file_instance:
                old_path = file_instance.name
                ext = old_path.split('.')[-1]
                new_path = f"{self.user_id}/{file_field}.{ext}"
                if old_path.startswith("temp/") and old_path != new_path:
                    with default_storage.open(old_path, 'rb') as file_content:
                        default_storage.save(new_path, ContentFile(file_content.read()))
                    default_storage.delete(old_path)
                    setattr(self, file_field, new_path)
                    super().save(update_fields=[file_field])

    def delete(self, *args, **kwargs):
        """Delete the user's folder and all files inside it when the user is deleted."""
        user_folder = os.path.join(settings.MEDIA_ROOT, str(self.user_id))
        if os.path.exists(user_folder) and os.path.isdir(user_folder):
            for file_name in os.listdir(user_folder):
                file_path = os.path.join(user_folder, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(user_folder)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id}"




class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    




class MeetingRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    #user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_requests',blank=True, null=True)
    user_id = models.ForeignKey(
        "users.User",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="agent_requests",
        blank=True,
        null=True
    )
    referral_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    department = models.ForeignKey(Department,on_delete=models.CASCADE,null=True,blank=True)
    requested_date = models.DateField()
    requested_time = models.TimeField()
    is_scheduled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} → {self.department.name} on {self.requested_date}"
    






class ScheduledMeeting(models.Model):
    scheduled_meeting_id = models.AutoField(primary_key=True)
    #request = models.OneToOneField(MeetingRequest, on_delete=models.CASCADE)
    #user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_scheduled_meetings',blank=True, null=True)
    request = models.OneToOneField(
        "users.MeetingRequest",   # ✅ STRING
        on_delete=models.CASCADE
    )

    user_id = models.ForeignKey(
        "users.User",             # ✅ STRING
        on_delete=models.CASCADE,
        related_name="agent_scheduled_meetings",
        blank=True,
        null=True
    )

    scheduled_by = models.ForeignKey(
        "users.User",             # ✅ STRING
        on_delete=models.SET_NULL,
        null=True,
        related_name="scheduled_meetings"
    )
    referral_id = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=200,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    #profile_type = models.CharField(max_length=200,blank=True, null=True)
    department = models.ForeignKey(Department,on_delete=models.CASCADE,null=True,blank=True)
    scheduled_date = models.DateField(blank=True, null=True)
    scheduled_time = models.TimeField(blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    #scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='scheduled_meetings')
    status_choices = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    status = models.CharField(max_length=20, choices=status_choices)
    notes = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.request.user_id} with {self.request.department.name} on {self.scheduled_date}"







class Lead(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    message = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"


class CarouselItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    #image = models.ImageField(upload_to='carousel/')
    image = models.ImageField(upload_to='carousel/', blank=True, null=True)
    video = models.FileField(upload_to='carousel/', blank=True, null=True)
    link = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title





  
class TrainingMaterial(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='training_materials/')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,null=True,blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
  



class HowItWorks(models.Model):
    title = models.CharField(max_length=255,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title
    

class Phonenumber(models.Model):
    name = models.CharField(max_length=255,blank=True, null=True)
    phone_number = models.CharField(max_length=16,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.id}"
    


class ChatKeyword(models.Model):
    keyword = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.keyword


class ChatResponse(models.Model):
    # question_number = models.PositiveIntegerField(unique=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return f"{self.id}"


class SiteVisit(models.Model):
    """
    Model to store details of a property site visit.
    """
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    # Agent Details
    #agent_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_site_visit')
    #user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_site_visit',blank=True, null=True)
    agent_id = models.ForeignKey(
        "users.User",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="agent_site_visit"
    )

    user_id = models.ForeignKey(
        "users.User",   # ✅ STRING
        on_delete=models.CASCADE,
        related_name="user_site_visit",
        blank=True,
        null=True
    )
    # Site Details
    site_name = models.CharField(max_length=100)
    site_owner_name = models.CharField(max_length=100)
    site_owner_mobile_number = models.CharField(max_length=15)
    site_owner_email = models.EmailField(blank=True, null=True)
    site_location = models.CharField(max_length=255)
    site_photo = models.ImageField(upload_to='site_visits', blank=True, null=True)
    # Customer Details
    customer_name = models.CharField(max_length=100)
    customer_mobile_number = models.CharField(max_length=15)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Visit"
        verbose_name_plural = "Site Visits"
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.customer_name} - {self.site_name} ({self.date})"







class ReferralPrefix(models.Model):
    prefix = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.prefix

   

class Like(models.Model):
    
    user = models.ForeignKey(
        "users.User",          # ✅ STRING
        on_delete=models.CASCADE
    )
    property = models.ForeignKey(
        "property.Property",   # ✅ STRING
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.id}"










class Wishlist(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    variant = models.ForeignKey(
        "business.ProductVariant",
        on_delete=models.CASCADE,
        related_name="wishlisted_variants",
        null=True,
        blank=True
    )

    property_item = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE,
        related_name="wishlisted_properties",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'variant'],
                name='unique_variant_wishlist',
                condition=models.Q(property_item__isnull=True)
            ),
            models.UniqueConstraint(
                fields=['user', 'property_item'],
                name='unique_property_wishlist',
                condition=models.Q(variant__isnull=True)
            ),
        ]

    def clean(self):
        if not self.variant and not self.property_item:
            raise ValidationError("Wishlist must have either variant or property item.")

        if self.variant and self.property_item:
            raise ValidationError("Wishlist cannot have both variant and property.")

    @property
    def product(self):
        return self.variant.product if self.variant else None

    def __str__(self):
        if self.variant:
            return f"{self.user} - {self.variant.sku}"
        return f"{self.user} - Property: {self.property_item.property_title}"

class Cart(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    variant = models.ForeignKey(
        "business.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_variants",
        null=True,
        blank=True
    )

    property_item = models.ForeignKey(
        "property.Property",
        on_delete=models.CASCADE,
        related_name="cart_properties",
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'variant'],
                name='unique_variant_cart',
                condition=models.Q(property_item__isnull=True)
            ),
            models.UniqueConstraint(
                fields=['user', 'property_item'],
                name='unique_property_cart',
                condition=models.Q(variant__isnull=True)
            ),
        ]

    def clean(self):
        if not self.variant and not self.property_item:
            raise ValidationError("Cart must have either variant or property.")

        if self.variant and self.property_item:
            raise ValidationError("Cart cannot have both variant and property.")

        if self.property_item and self.quantity != 1:
            raise ValidationError("Property quantity must be 1.")

        if self.variant:
            if self.quantity < 1:
                raise ValidationError("Variant quantity must be at least 1.")
            if self.quantity > self.variant.stock:
                raise ValidationError("Insufficient stock for this variant.")

    @property
    def price(self):
        if self.variant:
            return self.variant.selling_price or self.variant.mrp
        return self.property_item.total_property_value

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        if self.variant:
            return f"{self.user} - {self.variant.sku} x {self.quantity}"
        return f"{self.user} - Property: {self.property_item.title}"
