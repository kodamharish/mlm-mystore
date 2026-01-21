from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('login1/', LoginAPIView1.as_view(), name='login1'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),

    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:role_id>/', RoleDetailView.as_view(), name='role-detail'),

    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/search/', UserSearchAPIView.as_view(), name='users-search'),

    #path('users/role/<str:role_name>/', UsersByRoleAPIView.as_view(), name='users-by-role'), 
    #path('users/status/<str:user_status>/', UsersByStatus.as_view(), name='users-by-status'), 

    #path('agents/referral-id/<str:referral_id>/', AgentsByReferralIdAPIView.as_view(), name='agents-by-referral-id'), 
    path('counts/', CountAPIView.as_view(), name='counts'),

    path('send-otp/', SendOTPView.as_view(), name='send-otp'),   
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('verify-otp-reset-password/', VerifyOTPAndResetPasswordView.as_view(), name='verify-reset'),



    path('departments/', DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<int:id>/', DepartmentDetailView.as_view(), name='department-detail'),


    # path("meetings/", MeetingListCreateView.as_view()),
    # path("meetings/<int:meeting_id>/", MeetingDetailView.as_view()),

    path('meeting-requests/', MeetingRequestListCreateView.as_view(), name='meeting-requests'),
    path('meeting-requests/<int:request_id>/', MeetingRequestDetailView.as_view(), name='meeting-request-detail'),
    path('scheduled-meetings/', ScheduledMeetingListCreateView.as_view(), name='scheduled-meetings'),
    path('scheduled-meetings/<int:scheduled_meeting_id>/', ScheduledMeetingDetailView.as_view(), name='scheduled-meeting-detail'),
    path('meeting-requests/user-id/<int:user_id>/', MeetingRequestsByUserIdAPIView.as_view(), name='meeting-requests-user-id'),

    path('leads/', LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:id>/', LeadDetailView.as_view(), name='lead-detail'),

    path('carousel/', CarouselItemListCreateView.as_view(), name='carousel-list-create'),
    path('carousel/<int:pk>/', CarouselItemDetailView.as_view(), name='carousel-detail'),


    path('training-materials/', TrainingMaterialListCreateView.as_view(), name='training_material_list_create'),
    path('training-materials/<int:id>/', TrainingMaterialDetailView.as_view(), name='training_material_detail'),

    path("how-it-works/", HowItWorksListCreateView.as_view(), name="how_it_works_list_create"),
    path("how-it-works/<int:id>/", HowItWorksDetailView.as_view(), name="how_it_works_detail"),


    path('phonenumbers/', PhonenumberListCreateView.as_view(), name='phonenumber-list-create'),
    path('phonenumbers/<int:id>/', PhonenumberDetailView.as_view(), name='phonenumber-detail'),

    
    # Like APIs
    path('likes/', LikeListCreateView.as_view(), name='like-list-create'),
    path('likes/<int:like_id>/', LikeDetailView.as_view(), name='like-detail'),

    # Wishlist APIs
    path('wishlist/', WishlistListCreateView.as_view(), name='wishlist-list-create'),
    path('wishlist/<int:wishlist_id>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    path('wishlist/user-id/<int:user_id>/', WishlistByUserAPIView.as_view(), name='wishlist-by-user-id'),

    path("chatbot/", ChatBotAPIView.as_view(), name="chatbot"),
    path("responses/", ChatResponseListCreateAPIView.as_view(), name="responses"),
    path("responses/<int:pk>/", ChatResponseDetailView.as_view(), name="chatresponse-detail"),
    path("keywords/", ChatKeywordListCreateAPIView.as_view(), name="keywords"),

    path('site-visits/', SiteVisitListCreateView.as_view(), name='sitevisit-list-create'),
    path('site-visits/<int:visit_id>/', SiteVisitDetailView.as_view(), name='sitevisit-detail'),
    path('site-visits/user-id/<int:id>/', SiteVisitsByUserView.as_view(), name='sitevisits-by-user'),


    path('cart/', CartListCreateView.as_view()),
    path('cart/cart-id/<int:id>/', CartDetailView.as_view()),
    path('cart/user-id/<int:user_id>/', CartByUserAPIView.as_view()),

    path("referral-prefix/", ReferralPrefixListCreateView.as_view()),
    path("referral-prefix/<int:id>/", ReferralPrefixDetailView.as_view()),




]