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
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_variants(self, obj):
        request = self.context.get("request")
        qs = obj.variants.all()

        # If serializer used without request context → return all variants
        if request is None:
            return ProductVariantSerializer(qs, many=True).data

        params = request.query_params
        price_range = params.get("price_range")
        discount_range = params.get("discount_range")

        # ----- PRICE RANGE -----
        if price_range:
            ranges = {
            "0-500": (0, 500), # 0 ≤ price < 500
            "500-1000": (500, 1000), # 500 ≤ price < 1000
            "1000-5000": (1000, 5000),
            "5000-10000": (5000, 10000),
            "10000+": (10000, None),
            }

            if price_range in ranges:
                low, high = ranges[price_range]
                if high is None:
                    qs = qs.filter(selling_price__gte=low)
                else:
                    qs = qs.filter(selling_price__gte=low, selling_price__lte=high)

        # ----- DISCOUNT RANGE -----
        if discount_range:
            ranges = {
            "0-10": (0, 10),
            "10-20": (10, 20),
            "20-30": (20, 30),
            "30-40": (30, 40),
            "40-50": (40, 50),
            "50-60": (50, 60),
            "60+": (60, None),
            }

            if discount_range in ranges:
                low, high = ranges[discount_range]

                qs = qs.annotate(
                    discount=ExpressionWrapper(
                        ((F('mrp') - F('selling_price')) / F('mrp')) * 100,
                        output_field=DecimalField(max_digits=5, decimal_places=2)
                    )
                )

                if high is None:
                    qs = qs.filter(discount__gte=low)
                else:
                    qs = qs.filter(discount__gte=low, discount__lte=high)

        return ProductVariantSerializer(qs, many=True).data





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



