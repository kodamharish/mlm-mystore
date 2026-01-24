from django.urls import path
from .views import *

urlpatterns = [

    path('commissions-master/', CommissionMasterListCreateView.as_view(), name='commission-master-list-create'),
    path('commissions-master/<int:id>/', CommissionMasterDetailView.as_view(), name='commission-master-detail'),
    
    # Commission URLs
    # path('commissions/', CommissionListCreateView.as_view(), name='commission-list-create'),
    # path('commissions/<int:commission_id>/', CommissionDetailView.as_view(), name='commission-detail'),

    # path('company-commissions/referral-id/<str:referral_id>/', CommissionByReferralId.as_view(), name='commissions-referral-id'),

    # path('commission/distribute/<int:transaction_id>/', DistributeCommissionAPIView.as_view(), name='distribute-commission'),
    # path('commissions/preview/<int:transaction_id>/', CommissionPreviewAPIView.as_view(), name='commissions-preview'),

    # path('agent-commissions/user-id/<int:user_id>/', AgentCommissionAPIView.as_view(), name='agent-commissions'),
]