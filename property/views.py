# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from django.utils import timezone
from datetime import timedelta
#from transactions.models import *
from users.models import *
from users.serializers import *
from django.db.models import Q
from django.db.models import Sum
from .filters import PropertyFilter
from mlm.pagination import GlobalPagination


# ------------------ Property Category Views ------------------




class PropertyCategoryListCreateView(APIView):

    def get(self, request):
        try:
            categories = PropertyCategory.objects.all().order_by('-property_category_id')

            paginator = GlobalPagination()
            paginated_categories = paginator.paginate_queryset(
                categories,
                request
            )

            serializer = PropertyCategorySerializer(
                paginated_categories,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = PropertyCategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PropertyCategoryDetailView(APIView):
    def get_object(self, property_category_id):
        return get_object_or_404(PropertyCategory, property_category_id=property_category_id)

    def get(self, request, property_category_id):
        try:
            category = self.get_object(property_category_id)
            serializer = PropertyCategorySerializer(category)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, property_category_id):
        try:
            category = self.get_object(property_category_id)
            serializer = PropertyCategorySerializer(category, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, property_category_id):
        try:
            category = self.get_object(property_category_id)
            category.delete()
            return Response({"message": "Property category deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Property Type Views ------------------




class PropertyTypeListCreateView(APIView):

    def get(self, request):
        try:
            types = PropertyType.objects.all().order_by('-property_type_id')

            paginator = GlobalPagination()
            paginated_types = paginator.paginate_queryset(
                types,
                request
            )

            serializer = PropertyTypeSerializer(
                paginated_types,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = PropertyTypeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PropertyTypeDetailView(APIView):
    def get_object(self, property_type_id):
        return get_object_or_404(PropertyType, property_type_id=property_type_id)

    def get(self, request, property_type_id):
        try:
            prop_type = self.get_object(property_type_id)
            serializer = PropertyTypeSerializer(prop_type)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, property_type_id):
        try:
            prop_type = self.get_object(property_type_id)
            serializer = PropertyTypeSerializer(prop_type, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, property_type_id):
        try:
            prop_type = self.get_object(property_type_id)
            prop_type.delete()
            return Response({"message": "Property type deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Property Type by Category Name ------------------

class PropertyTypeByCategoryNameView(APIView):
    def get(self, request, category_name):
        try:
            category = PropertyCategory.objects.get(name__iexact=category_name)
            property_types = PropertyType.objects.filter(category=category)
            serializer = PropertyTypeSerializer(property_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PropertyCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Property Type by Category ID ------------------

class PropertyTypeByCategoryIDView(APIView):
    def get(self, request, category_id):
        try:
            category = PropertyCategory.objects.get(property_category_id=category_id)
            property_types = PropertyType.objects.filter(category=category)
            serializer = PropertyTypeSerializer(property_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PropertyCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Property Views ------------------



class PropertyListCreateView_old(APIView):

    def get(self, request):
        try:
            properties = Property.objects.all().order_by('-property_id')

            paginator = GlobalPagination()
            paginated_properties = paginator.paginate_queryset(properties, request)

            user_properties = (
                UserProperty.objects
                .select_related('user')
                .filter(property__in=paginated_properties)
            )

            # ✅ FIXED: Use property_id
            user_property_map = {
                up.property.property_id: up for up in user_properties
            }

            response_data = []

            for prop in paginated_properties:
                prop_data = PropertySerializer(prop).data

                up = user_property_map.get(prop.property_id)

                if up:
                    user_info = UserSerializer(up.user).data
                    prop_data["buyer_user"] = {
                        **user_info,
                        "booking_date": up.booking_date,
                        "purchase_date": up.purchase_date
                    }
                else:
                    prop_data["buyer_user"] = None

                response_data.append(prop_data)

            return paginator.get_paginated_response(response_data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = PropertySerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PropertyListCreateView(APIView):

    def get(self, request):
        try:
            # ---------------------------------------
            # 1️⃣ BASE QUERYSET
            # ---------------------------------------
            queryset = Property.objects.all()

            # ---------------------------------------
            # 2️⃣ ROLE-BASED FILTER (OPTIONAL)
            # ---------------------------------------
            role_name = request.GET.get('role')

            if role_name:
                try:
                    role = Role.objects.get(role_name__iexact=role_name)
                except Role.DoesNotExist:
                    return Response(
                        {"error": f"Role '{role_name}' not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                users_with_role = User.objects.filter(roles=role)
                queryset = queryset.filter(user_id__in=users_with_role)

            # ---------------------------------------
            # 3️⃣ APPLY PROPERTY FILTER (Django Filters)
            # ---------------------------------------
            filterset = PropertyFilter(data=request.GET, queryset=queryset)
            if not filterset.is_valid():
                return Response(
                    filterset.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = filterset.qs

            # ---------------------------------------
            # 4️⃣ APPLY ORDERING
            # ---------------------------------------
            ordering = request.GET.get('ordering')
            allowed = [
                'created_at', '-created_at',
                'total_property_value', '-total_property_value'
            ]
            queryset = queryset.order_by(ordering if ordering in allowed else '-created_at')

            # ---------------------------------------
            # 5️⃣ OPTIMIZE QUERYSET
            # ---------------------------------------
            queryset = queryset.select_related(
                'category', 'property_type'
            ).prefetch_related(
                'amenities'
            )

            # ---------------------------------------
            # 6️⃣ PAGINATION
            # ---------------------------------------
            paginator = GlobalPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = PropertySerializer(paginated_queryset, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = PropertySerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )






class GlobalNotificationListView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)

            statuses = UserNotificationStatus.objects.filter(user=user).select_related('notification')

            data = [
                {
                    "notification_id": s.notification.id,
                    "notification_status_id": s.id,
                    "message": s.notification.message,
                    "property": {
                        "id": s.notification.property.property_id,
                        "title": s.notification.property.property_title
                    },
                    "created_at": s.notification.created_at,
                    "is_read": s.is_read
                }
                for s in statuses.order_by('-notification__created_at')
            ]
            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        


class MarkNotificationReadView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        notification_id = request.data.get('notification_id')

        if not user_id or not notification_id:
            return Response({'error': 'user_id and notification_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(user_id=user_id)

            status_obj = UserNotificationStatus.objects.get(
                user=user,
                id=notification_id
            )
            status_obj.is_read = True
            status_obj.save()

            return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except UserNotificationStatus.DoesNotExist:
            return Response({'error': 'Notification not found for user'}, status=status.HTTP_404_NOT_FOUND)




class PropertyDetailView(APIView):

    def get_object(self, property_id):
        return get_object_or_404(Property, property_id=property_id)

    def get(self, request, property_id):
        try:
            property_instance = self.get_object(property_id)
            serializer = PropertySerializer(property_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, property_id):
        try:
            property_instance = self.get_object(property_id)

            # Store old approval status before updating
            old_status = property_instance.approval_status

            serializer = PropertySerializer(
                property_instance, 
                data=request.data, 
                partial=True, 
                context={'request': request}
            )

            if serializer.is_valid():
                updated_property = serializer.save()

                # 🔥 Trigger notification only if status changed to APPROVED
                if old_status != "approved" and updated_property.approval_status == "approved":
                    self.create_approval_notification(updated_property)

                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, property_id):
        try:
            property_instance = self.get_object(property_id)
            property_instance.delete()
            return Response({"message": "Property deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔥 NEW: Helper method to create notification only when approved
    def create_approval_notification(self, property_instance):
        added_by = property_instance.user_id  # User who added property

        # Notify all users except the property creator
        users_to_notify = User.objects.exclude(user_id=added_by.user_id)

        notification = Notification.objects.create(
            message=f"New: {property_instance.property_title}",
            property=property_instance
        )

        notification.visible_to_users.set(users_to_notify)

        # Create unread status for each user
        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(
                user=user, 
                notification=notification, 
                is_read=False
            )
            for user in users_to_notify
        ])






from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LatestPropertiesAPIView(APIView):
    """
    GET → List latest properties (last 30 days), optionally filtered by user (paginated)
    """

    def get(self, request, user_id=None):
        try:
            one_month_ago = timezone.now() - timedelta(days=30)

            if user_id:
                properties = (
                    Property.objects
                    .filter(user_id=user_id, created_at__gte=one_month_ago)
                    .order_by('-property_id')
                )
            else:
                properties = (
                    Property.objects
                    .filter(created_at__gte=one_month_ago)
                    .order_by('-property_id')
                )

            paginator = GlobalPagination()
            paginated_properties = paginator.paginate_queryset(
                properties,
                request
            )

            serializer = PropertySerializer(
                paginated_properties,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class PropertiesByUserID(APIView):
    """
    GET → List properties by user ID (paginated)
    """

    def get(self, request, user_id):
        try:
            properties = (
                Property.objects
                .filter(user_id=user_id)
                .order_by('-property_id')
            )

            paginator = GlobalPagination()
            paginated_properties = paginator.paginate_queryset(
                properties,
                request
            )

            serializer = PropertySerializer(
                paginated_properties,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PropertiesSoldByUserID(APIView):
    def get(self, request, user_id):
        try:
            properties = Property.objects.filter(user_id=user_id,status='sold')
            serializer = PropertySerializer(properties, many=True)  # <-- FIXED HERE
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        





class PropertiesPurchasedByUserID(APIView):
    def get(self, request, user_id):
        try:
            properties = Property.objects.filter(owner=user_id,status='sold')
            serializer = PropertySerializer(properties, many=True)  # <-- FIXED HERE
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertiesByApprovalStatus(APIView):
    def get(self, request, approval_status):
        try:
            properties = Property.objects.filter(approval_status=approval_status)
            response_data = []

            for prop in properties:
                # Serialize the property
                prop_data = PropertySerializer(prop).data
                buyer_data = None

                try:
                    # Prefer 'purchased' status first, fallback to 'booked'
                    user_property = (
                        prop.user_properties.filter(status='purchased').first()
                        or prop.user_properties.filter(status='booked').first()
                    )

                    if user_property:
                        user_info = UserSerializer(user_property.user).data
                        buyer_data = {
                            **user_info,
                            "booking_date": user_property.booking_date,
                            "purchase_date": user_property.purchase_date
                        }
                except UserProperty.DoesNotExist:
                    buyer_data = None

                # Add buyer_user to property data
                prop_data["buyer_user"] = buyer_data
                response_data.append(prop_data)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PropertiesByStatus(APIView):
    def get(self, request, property_status):
        try:
            properties = Property.objects.filter(status=property_status)
            response_data = []

            for prop in properties:
                # Serialize the property
                prop_data = PropertySerializer(prop).data
                buyer_data = None

                try:
                    # Prefer 'purchased' status first, fallback to 'booked'
                    user_property = (
                        prop.user_properties.filter(status='purchased').first()
                        or prop.user_properties.filter(status='booked').first()
                    )

                    if user_property:
                        user_info = UserSerializer(user_property.user).data
                        buyer_data = {
                            **user_info,
                            "booking_date": user_property.booking_date,
                            "purchase_date": user_property.purchase_date
                        }
                except UserProperty.DoesNotExist:
                    buyer_data = None

                # Add buyer_user to property data
                prop_data["buyer_user"] = buyer_data
                response_data.append(prop_data)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







#Working with Counts

class PropertyStatsAPIView(APIView):
    def get(self, request):
        data = {}
        one_month_ago = timezone.now() - timedelta(days=30)

        # --- Category-wise Stats ---
        categories = PropertyCategory.objects.all()
        for category in categories:
            listing_qs = Property.objects.filter(category=category)
            latest_qs = listing_qs.filter(created_at__gte=one_month_ago)

            data[category.name] = {
                "listing_count": listing_qs.count(),
                "latest_count": latest_qs.count(),
                "sold": listing_qs.filter(status="sold").count(),
                "booked": listing_qs.filter(status="booked").count(),
                "available": listing_qs.filter(status="available").count(),
                "pending": listing_qs.filter(approval_status="pending").count(),
                "approved": listing_qs.filter(approval_status="approved").count(),
                "rejected": listing_qs.filter(approval_status="rejected").count(),
            }

        # --- Type-wise Stats ---
        types = PropertyType.objects.all()
        for prop_type in types:
            listing_qs = Property.objects.filter(property_type=prop_type)
            latest_qs = listing_qs.filter(created_at__gte=one_month_ago)

            data[prop_type.name] = {
                "listing_count": listing_qs.count(),
                "latest_count": latest_qs.count(),
                "sold": listing_qs.filter(status="sold").count(),
                "booked": listing_qs.filter(status="booked").count(),
                "available": listing_qs.filter(status="available").count(),
                "pending": listing_qs.filter(approval_status="pending").count(),
                "approved": listing_qs.filter(approval_status="approved").count(),
                "rejected": listing_qs.filter(approval_status="rejected").count(),
            }

        # --- Global Stats ---
        # for status_value in ['sold', 'booked', 'available']:
        #     data[status_value] = {
        #         "count": Property.objects.filter(status=status_value).count()
        #     }

        # for approval_value in ['pending', 'approved', 'rejected']:
        #     data[approval_value] = {
        #         "count": Property.objects.filter(approval_status=approval_value).count()
        #     }

        return Response(data, status=status.HTTP_200_OK)





class PropertyStatsByUserAPIView(APIView):
    def get(self, request, user_id):
        data = {}
        one_month_ago = timezone.now() - timedelta(days=30)

        # =====================================================
        # A. PROPERTIES ADDED BY USER (SELLER VIEW)
        # =====================================================
        added_properties = Property.objects.filter(user_id=user_id)

        data["added"] = {
            "total": added_properties.count(),
            "list": PropertySerializer(added_properties, many=True).data
        }

        # Latest added (last 30 days)
        latest_added = added_properties.filter(created_at__gte=one_month_ago)
        data["added_latest"] = {
            "count": latest_added.count(),
            "list": PropertySerializer(latest_added, many=True).data
        }

        # Status-wise (sold / booked / available) — ADDED BY USER
        data["added_status"] = {}

        for status_value in ['sold', 'booked', 'available']:
            qs = added_properties.filter(status=status_value)
            enriched_list = []

            for prop in qs:
                prop_data = PropertySerializer(prop).data
                buyer_data = None

                if status_value in ['sold', 'booked']:
                    up_status = 'purchased' if status_value == 'sold' else 'booked'
                    user_prop = UserProperty.objects.filter(
                        property=prop,
                        status=up_status
                    ).select_related('user').first()

                    if user_prop:
                        buyer_data = {
                            "buyer": UserSerializer(user_prop.user).data,
                            "booking_date": user_prop.booking_date,
                            "purchase_date": user_prop.purchase_date
                        }

                prop_data["buyer_details"] = buyer_data
                enriched_list.append(prop_data)

            data["added_status"][status_value] = {
                "count": qs.count(),
                "list": enriched_list
            }

        # =====================================================
        # B. PROPERTIES BOOKED / PURCHASED BY USER (BUYER VIEW)
        # =====================================================
        user_properties = UserProperty.objects.filter(user_id=user_id)

        data["buyer"] = {}

        # Booked by user
        booked_entries = user_properties.filter(status='booked')
        data["buyer"]["booked"] = {
            "count": booked_entries.count(),
            "list": PropertySerializer(
                [up.property for up in booked_entries],
                many=True
            ).data
        }

        # Purchased by user
        purchased_entries = user_properties.filter(status='purchased')
        data["buyer"]["purchased"] = {
            "count": purchased_entries.count(),
            "list": PropertySerializer(
                [up.property for up in purchased_entries],
                many=True
            ).data
        }

        # =====================================================
        # C. APPROVAL STATUS (FOR ADDED PROPERTIES)
        # =====================================================
        data["approval"] = {}

        for approval_status in ['pending', 'approved', 'rejected']:
            qs = added_properties.filter(approval_status=approval_status)
            data["approval"][approval_status] = {
                "count": qs.count(),
                "list": PropertySerializer(qs, many=True).data
            }

        return Response(data, status=status.HTTP_200_OK)


class UniversalPropertySearchAPIView(APIView):
    def get(self, request):
        try:
            query = request.query_params.get('q', '').strip()
            looking_to = request.query_params.get('looking_to', '').strip().lower()

            if not looking_to:
                return Response({"error": "Query parameter `looking_to` is required."}, status=status.HTTP_400_BAD_REQUEST)

            filters = Q(looking_to__iexact=looking_to)

            if query:
                filters &= (
                    Q(property_id__icontains=query) |
                    Q(property_title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(address__icontains=query) |
                    Q(city__icontains=query) |
                    Q(state__icontains=query) |
                    Q(country__icontains=query) |
                    Q(pin_code__icontains=query) |
                    Q(latitude__icontains=query) |
                    Q(longitude__icontains=query) |
                    Q(plot_area_sqft__icontains=query) |
                    Q(builtup_area_sqft__icontains=query) |
                    Q(length_ft__icontains=query) |
                    Q(breadth_ft__icontains=query) |
                    Q(number_of_floors__icontains=query) |
                    Q(number_of_open_sides__icontains=query) |
                    Q(number_of_roads__icontains=query) |
                    Q(number_of_bedrooms__icontains=query) |
                    Q(number_of_balconies__icontains=query) |
                    Q(number_of_bathrooms__icontains=query) |
                    Q(road_width_1_ft__icontains=query) |
                    Q(road_width_2_ft__icontains=query) |
                    Q(facing__icontains=query) |
                    Q(ownership_type__icontains=query) |
                    Q(property_value__icontains=query) |
                    Q(total_property_value__icontains=query) |
                    Q(booking_amount__icontains=query) |
                    Q(property_uniqueness__icontains=query) |
                    Q(location_advantages__icontains=query) |
                    Q(other_features__icontains=query) |
                    Q(owner_name__icontains=query) |
                    Q(owner_contact__icontains=query) |
                    Q(owner_email__icontains=query) |
                    Q(role__icontains=query) |
                    Q(username__icontains=query) |
                    Q(referral_id__icontains=query) |
                    Q(agent_commission__icontains=query) |
                    Q(agent_commission_paid__icontains=query) |
                    Q(agent_commission_balance__icontains=query) |
                    Q(company_commission__icontains=query) |
                    Q(remaining_company_commission__icontains=query) |
                    Q(total_company_commission_distributed__icontains=query) |
                    Q(company_commission_status__icontains=query) |
                    Q(status__icontains=query) |
                    Q(approval_status__icontains=query) |
                    Q(category__name__icontains=query) |
                    Q(property_type__name__icontains=query) |
                    Q(user_id__username__icontains=query) |
                    Q(user_id__email__icontains=query) |
                    Q(amenities__name__icontains=query)
                )

            properties = Property.objects.filter(filters).distinct()
            serializer = PropertySerializer(properties, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Amenity Views ------------------



class AmenityListCreateView(APIView):

    def get(self, request):
        try:
            amenities = Amenity.objects.all().order_by('-amenity_id')

            paginator = GlobalPagination()
            paginated_amenities = paginator.paginate_queryset(
                amenities,
                request
            )

            serializer = AmenitySerializer(
                paginated_amenities,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = AmenitySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AmenityDetailView(APIView):
    def get_object(self, amenity_id):
        return get_object_or_404(Amenity, amenity_id=amenity_id)

    def get(self, request, amenity_id):
        try:
            amenity = self.get_object(amenity_id)
            serializer = AmenitySerializer(amenity)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, amenity_id):
        try:
            amenity = self.get_object(amenity_id)
            serializer = AmenitySerializer(amenity, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, amenity_id):
        try:
            amenity = self.get_object(amenity_id)
            amenity.delete()
            return Response({"message": "Amenity deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#EMI 
class EMIOptionListCreateAPIView(APIView):
    def get(self, request):
        options = EMIOption.objects.all()
        serializer = EMIOptionSerializer(options, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EMIOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # emi_amount auto-calculated
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EMIOptionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(EMIOption, pk=pk)

    def get(self, request, pk):
        emi_option = self.get_object(pk)
        serializer = EMIOptionSerializer(emi_option)
        return Response(serializer.data)

    def put(self, request, pk):
        emi_option = self.get_object(pk)
        serializer = EMIOptionSerializer(emi_option, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()  # Recalculate emi_amount
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        emi_option = self.get_object(pk)
        emi_option.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserEMIListCreateAPIView(APIView):
    def get(self, request):
        emis = UserEMI.objects.all()
        serializer = UserEMISerializer(emis, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserEMISerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # end_date auto-calculated
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserEMIDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(UserEMI, pk=pk)

    def get(self, request, pk):
        user_emi = self.get_object(pk)
        serializer = UserEMISerializer(user_emi)
        return Response(serializer.data)

    def put(self, request, pk):
        user_emi = self.get_object(pk)
        serializer = UserEMISerializer(user_emi, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()  # end_date recalculated
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user_emi = self.get_object(pk)
        user_emi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookingAmountSlabListCreateAPIView(APIView):
    def get(self, request):
        slabs = BookingAmountSlab.objects.all()
        serializer = BookingAmountSlabSerializer(slabs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookingAmountSlabSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingAmountSlabDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(BookingAmountSlab, pk=pk)

    def get(self, request, pk):
        slab = self.get_object(pk)
        serializer = BookingAmountSlabSerializer(slab)
        return Response(serializer.data)

    def put(self, request, pk):
        slab = self.get_object(pk)
        serializer = BookingAmountSlabSerializer(slab, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        slab = self.get_object(pk)
        slab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommissionSummaryAPIView(APIView):
    def get(self, request, user_id=None):
        try:
            if user_id:
                properties = Property.objects.filter(user_id=user_id)

                totals = properties.aggregate(
                    total_agent_commission=Sum('agent_commission'),
                    total_agent_commission_paid=Sum('agent_commission_paid'),
                    total_agent_commission_balance=Sum('agent_commission_balance'),
                    total_company_commission=Sum('company_commission'),
                    total_company_commission_paid=Sum('total_company_commission_distributed'),
                    total_company_commission_balance=Sum('remaining_company_commission'),
                )

                for key in totals:
                    totals[key] = totals[key] if totals[key] is not None else 0.00

                return Response({
                    'user_id': user_id,
                    'total_agent_commission': totals['total_agent_commission'],
                    'total_agent_commission_paid': totals['total_agent_commission_paid'],
                    'total_agent_commission_balance': totals['total_agent_commission_balance'],
                    'total_company_commission': totals['total_company_commission'],
                    'total_company_commission_paid': totals['total_company_commission_paid'],
                    'total_company_commission_balance': totals['total_company_commission_balance'],
                }, status=status.HTTP_200_OK)

            else:
                user_summaries = []
                user_ids = Property.objects.values_list('user_id', flat=True).distinct()

                for uid in user_ids:
                    user_properties = Property.objects.filter(user_id=uid)
                    totals = user_properties.aggregate(
                        total_agent_commission=Sum('agent_commission'),
                        total_agent_commission_paid=Sum('agent_commission_paid'),
                        total_agent_commission_balance=Sum('agent_commission_balance'),
                        total_company_commission=Sum('company_commission'),
                        total_company_commission_paid=Sum('total_company_commission_distributed'),
                        total_company_commission_balance=Sum('remaining_company_commission'),
                    )

                    for key in totals:
                        totals[key] = totals[key] if totals[key] is not None else 0.00

                    user = User.objects.filter(pk=uid).first()
                    user_summaries.append({
                        'user_id': uid,
                        'user_name': user.username if user else "Unknown",
                        'total_agent_commission': totals['total_agent_commission'],
                        'total_agent_commission_paid': totals['total_agent_commission_paid'],
                        'total_agent_commission_balance': totals['total_agent_commission_balance'],
                        'total_company_commission': totals['total_company_commission'],
                        'total_company_commission_paid': totals['total_company_commission_paid'],
                        'total_company_commission_balance': totals['total_company_commission_balance'],
                    })

                return Response(user_summaries, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#New

class PropertiesByRoleAPIView(APIView):
    def get(self, request, role_name):
        try:
            # Check if role exists
            try:
                role = Role.objects.get(role_name=role_name)
            except Role.DoesNotExist:
                return Response(
                    {"error": f"Role '{role_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get all users with this role
            users_with_role = User.objects.filter(roles=role)

            # Get properties added by those users
            properties = Property.objects.filter(user_id__in=users_with_role)

            serializer = PropertySerializer(properties, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )









class PropertySearchAPIView(APIView):

    def get(self, request):
        try:
            # -------------------------------------------------
            # 1️⃣ PURE BASE QUERYSET
            # -------------------------------------------------
            queryset = Property.objects.all()

            # -------------------------------------------------
            # 2️⃣ ROLE-BASED FILTER (OPTIONAL)
            # -------------------------------------------------
            role_name = request.GET.get('role')

            if role_name:
                try:
                    role = Role.objects.get(role_name__iexact=role_name)
                except Role.DoesNotExist:
                    return Response(
                        {"error": f"Role '{role_name}' not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                users_with_role = User.objects.filter(roles=role)

                queryset = queryset.filter(user_id__in=users_with_role)

            # -------------------------------------------------
            # 3️⃣ APPLY DJANGO FILTERS
            # -------------------------------------------------
            filterset = PropertyFilter(
                data=request.GET,
                queryset=queryset
            )

            if not filterset.is_valid():
                return Response(
                    filterset.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = filterset.qs

            # -------------------------------------------------
            # 4️⃣ OPTIMIZE QUERYSET (AFTER FILTERING)
            # -------------------------------------------------
            queryset = queryset.select_related(
                'category',
                'property_type'
            ).prefetch_related(
                'amenities'
            )

            # -------------------------------------------------
            # 5️⃣ ORDERING
            # -------------------------------------------------
            ordering = request.GET.get('ordering')
            allowed = [
                'created_at', '-created_at',
                'total_property_value', '-total_property_value'
            ]

            queryset = queryset.order_by(
                ordering if ordering in allowed else '-created_at'
            )

            # -------------------------------------------------
            # 6️⃣ PAGINATION
            # -------------------------------------------------
            paginator = GlobalPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = PropertyFullSerializer(
                paginated_queryset,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





