# subscriptions/serializers.py
from rest_framework import serializers
from .models import *
from rest_framework import serializers


# Serializer for creating and viewing the base plan (e.g., Connect+)
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['plan_id', 'plan_name', 'description','user_type']


# Serializer for creating and viewing specific plan variants (e.g., Connect+ 45 days)
class SubscriptionPlanVariantSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.plan_name', read_only=True)

    class Meta:
        model = SubscriptionPlanVariant
        fields = [
            'variant_id',
            'plan_id',            # FK: SubscriptionPlan ID
            'plan_name',       # Read-only
            'duration_in_days',
            'price',
            'original_price',
            'contact_limit',
            'priority_support',
            'instant_alerts',
            'relationship_manager'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user_id.email', read_only=True)
    plan_name = serializers.CharField(
        source='subscription_variant.plan_id.plan_name', read_only=True
    )
    duration_in_days = serializers.IntegerField(
        source='subscription_variant.duration_in_days', read_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            'subscription_id',
            'user_id',
            'user_email',
            'subscription_variant',
            'plan_name',
            'duration_in_days',
            'subscription_status',
            'subscription_start_datetime',   # ✅ correct
            'subscription_end_datetime',     # ✅ correct
        ]
        extra_kwargs = {
            'subscription_start_datetime': {'read_only': True},
            'subscription_end_datetime': {'read_only': True},
        }
