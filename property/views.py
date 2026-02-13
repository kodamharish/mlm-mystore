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
from .filters import *
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


class PropertyListCreateView(APIView):

    def get(self, request):
        try:
            queryset = Property.objects.all()

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

            filterset = PropertyFilter(data=request.GET, queryset=queryset)
            if not filterset.is_valid():
                return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

            queryset = filterset.qs

            ordering = request.GET.get('ordering')
            allowed = [
                'created_at', '-created_at',
                'total_property_value', '-total_property_value'
            ]
            queryset = queryset.order_by(ordering if ordering in allowed else '-created_at')

            queryset = queryset.select_related(
                'category', 'property_type'
            ).prefetch_related('amenities')

            paginator = GlobalPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = PropertySerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = PropertySerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                property_instance = serializer.save()

                # 🔥 Notify Admins on new property
                self.notify_admin_new_property(property_instance)

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔥 Admin Notification
    def notify_admin_new_property(self, property_instance):
        admin_users = User.objects.filter(roles__role_name="Admin").distinct()

        notification = Notification.objects.create(
            message=f"New Property Added: {property_instance.property_title}",
            property=property_instance
        )

        notification.visible_to_users.set(admin_users)

        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(user=user, notification=notification, is_read=False)
            for user in admin_users
        ])


class GlobalNotificationListView(APIView):
    """
    GET → List global notifications for a user (paginated)
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)

            statuses_qs = (
                UserNotificationStatus.objects
                .filter(user=user)
                .select_related('notification', 'notification__property')
                .order_by('-notification__created_at')
            )

            paginator = GlobalPagination()
            paginated_statuses = paginator.paginate_queryset(
                statuses_qs,
                request
            )

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
                for s in paginated_statuses
            ]

            return paginator.get_paginated_response(data)

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )






class NotificationListView(APIView):
    """
    GET → List notifications
    Optional filters:
        ?user=<id>
        ?is_read=true/false
    """

    def get(self, request):
        try:
            user_id = request.query_params.get("user")
            is_read_filter = request.query_params.get("is_read")

            statuses_qs = UserNotificationStatus.objects.all()

            # ✅ Filter by user (optional)
            if user_id:
                try:
                    user = User.objects.get(user_id=user_id)
                    statuses_qs = statuses_qs.filter(user=user)
                except User.DoesNotExist:
                    return Response(
                        {"error": "User not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # ✅ Filter by read/unread
            if is_read_filter is not None:
                if is_read_filter.lower() == "true":
                    statuses_qs = statuses_qs.filter(is_read=True)
                elif is_read_filter.lower() == "false":
                    statuses_qs = statuses_qs.filter(is_read=False)

            statuses_qs = statuses_qs.select_related(
                "notification",
                "notification__property",
                "notification__product_variant",
                "notification__product_variant__product"
            ).order_by("-notification__created_at")

            paginator = GlobalPagination()
            paginated_statuses = paginator.paginate_queryset(
                statuses_qs,
                request
            )

            data = []

            for s in paginated_statuses:
                notification = s.notification

                property_data = None
                product_data = None

                # ✅ Property Notification
                if notification.property:
                    property_data = {
                        "id": notification.property.property_id,
                        "title": notification.property.property_title
                    }

                # ✅ Product Variant Notification
                if notification.product_variant:
                    product_data = {
                        "variant_id": notification.product_variant.id,
                        "product_id": notification.product.product_id,
                        "product_name": notification.product_variant.product.product_name
                    }

                data.append({
                    "notification_status_id": s.id,
                    "notification_id": notification.id,
                    "message": notification.message,
                    "property": property_data,
                    "product": product_data,
                    "created_at": notification.created_at,
                    "is_read": s.is_read
                })

            # ✅ Read / Unread Counts
            read_count = None
            unread_count = None

            if user_id:
                read_count = UserNotificationStatus.objects.filter(
                    user_id=user_id,
                    is_read=True
                ).count()

                unread_count = UserNotificationStatus.objects.filter(
                    user_id=user_id,
                    is_read=False
                ).count()

            response = paginator.get_paginated_response(data)

            if user_id:
                response.data["read_count"] = read_count
                response.data["unread_count"] = unread_count

            return response

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class MarkNotificationReadView(APIView):

    def post(self, request):
        user_id = request.data.get("user_id")
        status_ids = request.data.get("notification_status_ids")

        if not user_id or not status_ids:
            return Response(
                {"error": "user_id and notification_status_ids required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        UserNotificationStatus.objects.filter(
            user_id=user_id,
            id__in=status_ids
        ).update(is_read=True)

        return Response(
            {"message": "Notifications marked as read"},
            status=status.HTTP_200_OK
        )






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
            old_status = property_instance.verification_status

            serializer = PropertySerializer(
                property_instance,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                updated_property = serializer.save()

                # 🔥 VERIFIED FLOW
                if old_status != "verified" and updated_property.verification_status == "verified":
                    self.notify_owner_verified(updated_property)
                    self.notify_agents_clients_verified(updated_property)

                # 🔥 REJECTED FLOW
                if old_status != "rejected" and updated_property.verification_status == "rejected":
                    self.notify_owner_rejected(updated_property)

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

    # 🔥 Owner Notification — Verified
    def notify_owner_verified(self, property_instance):
        owner = property_instance.user_id

        notification = Notification.objects.create(
            message=f"Your property '{property_instance.property_title}' has been verified.",
            property=property_instance
        )

        notification.visible_to_users.set([owner])

        UserNotificationStatus.objects.create(
            user=owner,
            notification=notification,
            is_read=False
        )

    # 🔥 Agents + Clients Notification
    def notify_agents_clients_verified(self, property_instance):
        owner = property_instance.user_id

        users_to_notify = User.objects.filter(
            roles__role_name__in=["Agent", "Client"]
        ).exclude(user_id=owner.user_id).distinct()

        notification = Notification.objects.create(
            message=f"New Verified Property Available: {property_instance.property_title}",
            property=property_instance
        )

        notification.visible_to_users.set(users_to_notify)

        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(user=user, notification=notification, is_read=False)
            for user in users_to_notify
        ])

    # 🔥 Owner Notification — Rejected
    def notify_owner_rejected(self, property_instance):
        owner = property_instance.user_id

        notification = Notification.objects.create(
            message=f"Your property '{property_instance.property_title}' was rejected.",
            property=property_instance
        )

        notification.visible_to_users.set([owner])

        UserNotificationStatus.objects.create(
            user=owner,
            notification=notification,
            is_read=False
        )








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


#New
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





