from django.urls import path
from .views import *
from .phonepe import *
from .phonepenew import *


urlpatterns = [
    
    path('transactions/', TransactionListCreateView.as_view() , name='transactions'),
    path('transactions/<int:transaction_id>/', TransactionDetailView.as_view(), name='transaction_details'),
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
    path("orders/", OrderListAPIView.as_view()),
    path("orders/<int:order_id>/", OrderDetailAPIView.as_view()),
    path("order-items/", OrderItemListAPIView.as_view()),
    path(
        "orders/<int:order_id>/confirm-cod/",
        ConfirmCODPaymentAPIView.as_view(),
        name="confirm-cod-payment"
    ),
    path(
        "orders/<int:order_id>/cancel/",
        CancelOrderAPIView.as_view(),
        name="cancel-order"
    ),

    path("orders-with-items/", OrderWithItemsAPIView.as_view()),
    path("users/<int:user_id>/order-summary/", UserOrderSummaryAPIView.as_view()),
    path("order-summary/", OrderSummaryAPIView.as_view()),
    path("admin-summary/", AdminSummaryAPIView.as_view()),
    path("summary/", AdminSummaryAPIView.as_view()),

    path("generate-invoice/", generate_invoice, name="generate_invoice"),
    



 
    
    

]