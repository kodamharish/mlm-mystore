from rest_framework import serializers
from .models import *


# ===========================
# BUSINESS
# ===========================
class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = "__all__"
        read_only_fields = (
            'verification_status',
            'verified_at',
            'created_at',
            'updated_at'
        )


# ===========================
# PRODUCT MEDIA
# ===========================
class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = "__all__"


# ===========================
# PRODUCT VARIANT
# ===========================
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"
        read_only_fields = ('selling_price', 'cgst_amount', 'sgst_amount')


# ===========================
# PRODUCT (NESTED READ)
# ===========================
class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"



#Old
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'category_id',
            'name',
            'slug',
            'level',
            'parent',
            'icon',
            'display_order',
            'is_active',
            'children'
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data





class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'



