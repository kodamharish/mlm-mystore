from rest_framework import serializers
from .models import *


# ===========================
# BUSINESS
# ===========================

class BusinessWorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessWorkingHour
        fields = ['id', 'day', 'opens_at', 'closes_at', 'is_closed']


class BusinessSerializer(serializers.ModelSerializer):
    working_hours = BusinessWorkingHourSerializer(many=True, required=False)

    class Meta:
        model = Business
        fields = "__all__"
        read_only_fields = (
            'verification_status',
            'verified_at',
            'created_at',
            'updated_at'
        )

    def create(self, validated_data):
        working_hours_data = validated_data.pop('working_hours', [])
        business = super().create(validated_data)

        for wh in working_hours_data:
            BusinessWorkingHour.objects.create(business=business, **wh)

        return business


    def update(self, instance, validated_data):
        working_hours_data = validated_data.pop('working_hours', None)

        business = super().update(instance, validated_data)

        if working_hours_data is not None:
            # Clear old working hours
            instance.working_hours.all().delete()

            # Recreate new ones
            for wh in working_hours_data:
                BusinessWorkingHour.objects.create(business=instance, **wh)

        return business



# ===========================
# PRODUCT MEDIA
# ===========================


# ===========================
# PRODUCT VARIANT
# ===========================

# ===========================
# PRODUCT (NESTED READ)
# ===========================



class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        #fields = ['id', 'media_type', 'file', 'is_primary', 'sort_order']
        fields = "__all__"


class ProductVariantSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = "__all__"
        read_only_fields = ('selling_price', 'cgst_amount', 'sgst_amount')


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    

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



