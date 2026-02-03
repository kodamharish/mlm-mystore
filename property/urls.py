from django.urls import path
from .views import *

urlpatterns = [



    path('property-categories/', PropertyCategoryListCreateView.as_view(), name='property-category-list-create'),
    path('property-categories/<int:property_category_id>/', PropertyCategoryDetailView.as_view(), name='property-category-detail'),

    path('property-types/', PropertyTypeListCreateView.as_view(), name='property-type-list-create'),
    path('property-types/<int:property_type_id>/', PropertyTypeDetailView.as_view(), name='property-type-detail'),
    path('property-types/category-name/<str:category_name>/', PropertyTypeByCategoryNameView.as_view(), name='property-types-by-category-name'),
    path('property-types/category-id/<int:category_id>/', PropertyTypeByCategoryIDView.as_view(), name='property-types-by-category-id'),

    path('amenities/', AmenityListCreateView.as_view(), name='amenity-list-create'),
    path('amenities/<int:amenity_id>/', AmenityDetailView.as_view(), name='amenity-detail'),

    path('property/', PropertyListCreateView.as_view(), name='property'),
    path('property/<int:property_id>/', PropertyDetailView.as_view(), name='property_details'),
    path('properties/', PropertyListCreateView.as_view(), name='property'),
    path('properties/<int:property_id>/', PropertyDetailView.as_view(), name='property_details'),
    path('properties/search/', PropertySearchAPIView.as_view(),name='properties-search'),

    
    path('property-stats/', PropertyStatsAPIView.as_view(), name='property-stats'),
    path('property-stats/user-id/<int:user_id>/', PropertyStatsByUserAPIView.as_view(), name='property-stats'),
    
    
    path('booking-slabs/', BookingAmountSlabListCreateAPIView.as_view(), name='booking-slab-list-create'),
    path('booking-slabs/<int:pk>/', BookingAmountSlabDetailAPIView.as_view(), name='booking-slab-detail'),

    
    path('notifications/user-id/<int:user_id>/', GlobalNotificationListView.as_view(), name='global-notification'),
    path('notifications/mark-as-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/mark-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),

    



    
 
]