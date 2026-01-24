from rest_framework import serializers
from .models import *
from property.serializers import *


class CommissionMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionMaster
        fields = '__all__'



# class CommissionSerializer(serializers.ModelSerializer):
#     level_no = serializers.IntegerField(source='percentage.level_no', read_only=True)
#     percentage_value = serializers.DecimalField(source='percentage.percentage', max_digits=5, decimal_places=2, read_only=True)
#     #property_id = PropertySerializer(read_only=True)

#     class Meta:
#         model = Commission
#         fields = [
#             'commission_id',
#             'transaction_id',
#             'agent_id',
#             'agent_name',
#             'amount',
#             'referral_id',
#             'property_id',
#             'date',
#             'level_no',
#             'percentage_value',
#             'buyer_user_id',
#             'buyer_username',
#             'property_name',
#             #'property_id '

#         ]