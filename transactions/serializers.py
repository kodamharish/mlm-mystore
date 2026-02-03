from rest_framework import serializers
from .models import *
import os
from datetime import datetime
from rest_framework import serializers
from .models import Transaction
from business.serializers import *
from property.serializers import *


class OrderItemSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    property_details = PropertySerializer(source='property_item', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant",
            "variant_details",
            "property_item",
            "property_details",
            "quantity",
            "price",
        ]



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "user",
            "user_name",
            "total_amount",
            "status",
            "created_at",
            "items",
        ]



class TransactionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        doc_file = request.FILES.get('document_file') if request else None

        
        if doc_file:
            ext = os.path.splitext(doc_file.name)[1]
            doc_file.name = f"{self.doc_number}{ext}"
            validated_data['document_file'] = doc_file

        #validated_data['document_type'] = doc_type
        #validated_data['document_number'] = doc_number

        return Transaction.objects.create(**validated_data)



class OrderItemNestedSerializer(serializers.ModelSerializer):
    item_type = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_type",
            "item_name",
            "quantity",
            "price",
            "get_subtotal",
        ]

    def get_item_type(self, obj):
        if obj.variant:
            return "product"
        return "property"

    def get_item_name(self, obj):
        if obj.variant:
            return obj.variant.product.product_name
        return obj.property_item.property_title


class OrderWithItemsSerializer(serializers.ModelSerializer):
    items = OrderItemNestedSerializer(many=True, read_only=True)
    # user_name = serializers.CharField(source="user.first_name", read_only=True)
    user_id = serializers.CharField(source="user.user_id", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "user_id",
            "total_amount",
            "status",
            "created_at",
            "items",
        ]


