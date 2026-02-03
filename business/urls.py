from django.urls import path
from .views import *

urlpatterns = [
    

    path('categories/', CategoryListCreateView.as_view(),name='categories'),
    path('categories/<int:category_id>/', CategoryDetailView.as_view(),name='categories-detail'),
    path("categories/bulk/", CategoryBulkCreateView.as_view()),
    path('business/', BusinessListCreateView.as_view(), name='business-list-create'),
    path('business/<int:business_id>/', BusinessDetailView.as_view(), name='business-detail'),
    path('business/user-id/<int:id>/', BusinessByUserIDView.as_view(), name='business-by-user-id'),
    path('offers/', OfferListCreateView.as_view(), name='offer-list'),
    path('offers/<int:id>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/user-id/<int:user_id>/', OfferByUserView.as_view()),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/business-id/<int:business_id>/', ProductByBusinessView.as_view(), name='product-by-business-id'),

    




]