from django.urls import path
from .views import *
from .phonepe import *
from .phonepenew import *


urlpatterns = [
    
    path('transactions/', TransactionListCreateView.as_view() , name='transactions'),
    path('transactions/<int:transaction_id>/', TransactionDetailView.as_view(), name='transaction_details'),
    path('transactions/property/<int:property_id>/', TransactionByPropertyId.as_view(), name='transaction-by-property-id'),
    path('transactions/user-id/<int:user_id>/', TransactionByUserId.as_view(), name='transactions-by-user-id'),
    path('transactions/user-id/<int:user_id>/<str:transaction_for>/', PropertyOrSubcriptionTransactionByUserId.as_view(), name='property-or-subcription-transactions-by-user-id'),
    path('transactions/<str:transaction_for>/', PropertyOrSubcriptionTransactions.as_view(), name='property-or-subcription-transactions'),


    path('transactions/user-id/<int:user_id>/property-id/<int:property_id>/', TransactionByUserIdAndPropertyId.as_view(), name='transactions-by-user-id-property-id'),

    path('transactions/user-id/<int:user_id>/payment-type/<str:payment_type>/', TransactionByUserIdAndPaymentType.as_view(), name='transactions-by-user-id-payment-type'),
    path('transactions/payment-type/<str:payment_type>/', TransactionByPaymentType.as_view(), name='transactions-by-payment-type'),
    path('transactions/user-role/<str:role>/payment-type/<str:payment_type>/', TransactionByUserRolePaymentType.as_view(), name='transactions-by-user-role-payment-type'),

    path('transactions/user-id/<int:user_id>/property-id/<int:property_id>/payment-type/<str:payment_type>/', TransactionByUserIdPropertyIdAndPaymentType.as_view(), name='transactions-by-user-id-property-id-payment-type'),
    path('transactions/property-id/<int:property_id>/payment-type/<str:payment_type>/', TransactionByPropertyIdAndPaymentType.as_view(), name='transactions-by-property-id-payment-type'),

    path('transactions/grouped/user-id/<int:user_id>/', TransactionsGroupedByPaymentTypeAPIView.as_view(), name='grouped-transactions'),

    path('initiate-payment/', InitiatePaymentAPIView.as_view(), name='initiate-payment'),
    path('payment-status/', PaymentStatusAPIView.as_view(), name='payment-status'),

    path('subscription/initiate-payment/', SubscriptionInitiatePaymentAPIView.as_view(), name='new-initiate-payment'),
    #path('subscription/payment-status/', SubscriptionConfirmPaymentAPIView.as_view(), name='new-payment-status'),
    path('subscription/confirm-payment/', SubscriptionConfirmPaymentAPIView.as_view(), name='new-payment-status'),


    path('property/initiate-payment/', PropertyInitiatePaymentAPIView.as_view()),
    path('property/confirm-payment/', PropertyConfirmPaymentAPIView.as_view()),


    path('product/initiate-payment/', ProductInitiatePaymentAPIView.as_view()),
    path('product/confirm-payment/', ProductConfirmPaymentAPIView.as_view()),


    path('pay/agent-commission/', AgentCommissionTransactionAPIView.as_view()),



    # USER
    path("orders/user-id/<int:user_id>/", UserOrderListAPIView.as_view()),
    path("orders/order-id/<int:order_id>/items/", OrderItemByOrderAPIView.as_view()),

    # ADMIN
    path("orders/", OrderListAPIView.as_view()),
    path("orders/order-id/<int:order_id>/", OrderDetailAPIView.as_view()),
    path("order-items/", OrderItemListAPIView.as_view()),


 
    
    

]