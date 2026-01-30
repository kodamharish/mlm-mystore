from rest_framework import serializers
from .models import *

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)  # For response
    role_ids = serializers.PrimaryKeyRelatedField(     # For creating/updating
        queryset=Role.objects.all(), write_only=True, many=True, source="roles"
    )
    referral_id = serializers.CharField(read_only=True)  # Include in response, not required from input
    #referred_by = serializers.CharField(read_only=True)  # Include in response, not required from input
    level_no = serializers.CharField(read_only=True)  # Include in response, not required from input


    class Meta:
        model = User
        fields = '__all__'





class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


# class MeetingSerializer(serializers.ModelSerializer):
#     users = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=User.objects.all(),
#         required=False
#     )

#     class Meta:
#         model = Meeting
#         fields = "__all__"

#     def create(self, validated_data):
#         user_ids = self.initial_data.get("user_ids", [])
#         validated_data.pop("users", None)

#         meeting = Meeting.objects.create(**validated_data)
#         meeting.users.set(user_ids)
#         return meeting

#     def update(self, instance, validated_data):
#         user_ids = self.initial_data.get("user_ids", None)
#         validated_data.pop("users", None)

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         if user_ids is not None:
#             meeting.users.set(user_ids)

#         return instance



class MeetingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRequest
        fields = '__all__'

class ScheduledMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledMeeting
        fields = '__all__'



class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'


class CarouselItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselItem
        fields = '__all__'


class TrainingMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingMaterial
        fields = '__all__'


class HowItWorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = HowItWorks
        fields = '__all__'


class PhonenumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phonenumber
        fields = '__all__'




    


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'


# class WishlistSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Wishlist
#         fields = '__all__'






class ChatResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatResponse
        fields = "__all__"


class ChatKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatKeyword
        fields = "__all__"


class SiteVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteVisit
        fields = '__all__'







class ReferralPrefixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralPrefix
        fields = "__all__"


from property.serializers import PropertySerializer

# class WishlistSerializer(serializers.ModelSerializer):
#     property_details = PropertySerializer(source='property', read_only=True)

#     class Meta:
#         model = Wishlist
#         fields = ['id', 'user', 'property', 'property_details', 'product','created_at']


# class CartSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Cart
#         fields = '__all__'






from rest_framework import serializers
from property.serializers import PropertySerializer
from business.serializers import ProductVariantSerializer
from .models import Wishlist

class WishlistSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    property_details = PropertySerializer(source='property_item', read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            'id',
            'user',
            'variant',
            'variant_details',
            'property_item',
            'property_details',
            'created_at'
        ]


from rest_framework import serializers
from property.serializers import PropertySerializer
from business.serializers import ProductVariantSerializer
from .models import Cart

class CartSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    property_details = PropertySerializer(source='property_item', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'variant',
            'variant_details',
            'property_item',
            'property_details',
            'quantity',
            'subtotal',
            'created_at'
        ]

    def get_subtotal(self, obj):
        return obj.subtotal



