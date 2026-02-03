from django.urls import path
from .views import *



urlpatterns = [
    
    # Plans
    path('subscription/plans/', SubscriptionPlanListCreateView.as_view(), name='subscription-plans'),
    path('subscription/plans/<int:pk>/', SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),

    # Plan Variants
    path('subscription/plan-variants/', SubscriptionPlanVariantListCreateView.as_view(), name='plan-variants'),
    path('subscription/plan-variants/<int:pk>/', SubscriptionPlanVariantDetailView.as_view(), name='plan-variant-detail'),

    # Subscriptions
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscribe-user'),
    path('subscriptions/<int:subscription_id>/', SubscriptionDetailView.as_view(), name='subscription-detail'),

    path('user-subscriptions/user-id/<int:user_id>/', UserSubscriptionsView.as_view(), name='user-subscriptions'),


    path('subscription/plans/<str:user_type>/', SubscriptionPlanByUserTypeView.as_view(), name='subscription-plan-by-user-type'),
    path('subscription/plan-variants/<str:user_type>/', SubscriptionPlanVariantByUserTypeView.as_view(), name='subscription-plan-variant-by-user-type'),

    path('subscriptions/search/', SubscriptionSearchAPIView.as_view(), name='subscriptions-search'),
    path('subscriptions/analytics/', SubscriptionAnalyticsAPIView.as_view(), name='subscriptions-analytics'),

]








