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
    path('properties/user-id/<int:user_id>/', PropertiesByUserID.as_view(), name='properties-user-id'),
    path('properties/sold/user-id/<int:user_id>/', PropertiesSoldByUserID.as_view(), name='properties-sold-user-id'),
    path('properties/purchased/user-id/<int:user_id>/', PropertiesPurchasedByUserID.as_view(), name='properties-purchased-user-id'),


    path('properties/approval-status/<str:approval_status>/', PropertiesByApprovalStatus.as_view(), name='properties-approval-status'),
    path('properties/status/<str:property_status>/', PropertiesByStatus.as_view(), name='properties-status'),
    path('property-stats/', PropertyStatsAPIView.as_view(), name='property-stats'),
    path('property-stats/user-id/<int:user_id>/', PropertyStatsByUserAPIView.as_view(), name='property-stats'),
    path('properties/search/old/', UniversalPropertySearchAPIView.as_view(), name='universal-property-search'),
    
    path('booking-slabs/', BookingAmountSlabListCreateAPIView.as_view(), name='booking-slab-list-create'),
    path('booking-slabs/<int:pk>/', BookingAmountSlabDetailAPIView.as_view(), name='booking-slab-detail'),

    path('latest-properties/', LatestPropertiesAPIView.as_view(), name='new-properties'),
    path('latest-properties/user-id/<int:user_id>/', LatestPropertiesAPIView.as_view(), name='latest-properties-user'),

    path('emi-options/', EMIOptionListCreateAPIView.as_view(), name='emi-option-list-create'),
    path('emi-options/<int:pk>/', EMIOptionDetailAPIView.as_view(), name='emi-option-detail'),
    
    path('user-emis/', UserEMIListCreateAPIView.as_view(), name='user-emi-list-create'),
    path('user-emis/<int:pk>/', UserEMIDetailAPIView.as_view(), name='user-emi-detail'),

    path('notifications/user-id/<int:user_id>/', GlobalNotificationListView.as_view(), name='global-notification'),
    path('notifications/mark-as-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),

    path('commission-summary/', CommissionSummaryAPIView.as_view(), name='commission-summary-all'),
    path('commission-summary/<int:user_id>/', CommissionSummaryAPIView.as_view(), name='commission-summary-user'),

    #path("properties/by-role/<str:role_name>/", PropertiesByRoleAPIView.as_view(),name='properties-by-role'),



    #path('properties/search/', PropertySearchAPIView.as_view(),name='properties-search'),


    
 
]