from django.db import models
from property.models import *
#from transactions.models import *
from users.models import *

class CommissionMaster(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key
    level_no = models.IntegerField()  # Level number (1 to 10)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Commission percentage
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.id}"


# class Commission(models.Model):
#     commission_id = models.AutoField(primary_key=True)
#     percentage = models.ForeignKey(CommissionMaster, on_delete=models.CASCADE, related_name='company_commissions')
#     transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='company_commissions')
#     agent_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_company_commissions')
#     buyer_user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='buyer_id')
#     property_id = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='company_commissions')
#     agent_name = models.CharField(max_length=200, blank=True, null=True)
#     property_name = models.CharField(max_length=200, blank=True, null=True)
#     buyer_username = models.CharField(max_length=200, blank=True, null=True)
#     amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     referral_id = models.CharField(max_length=200, blank=True, null=True)
#     date = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Commission {self.commission_id} - {self.amount}"



