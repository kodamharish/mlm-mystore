from django.shortcuts import render
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from users.models import *  # Import your custom user model if needed
#from transactions.models import *
from mlm.pagination import GlobalPagination
from django.utils import timezone
from django.db.models import Count
from .models import Subscription
from .filters import *
#from common.pagination import GlobalPagination

# ------------------ Subscription Plan ------------------


# List and Create Subscription Plans (e.g., Connect, Connect+, Relax)


class SubscriptionPlanListCreateView(APIView):

    def get(self, request):
        try:
            plans = SubscriptionPlan.objects.all().order_by('-plan_id')

            paginator = GlobalPagination()
            paginated_plans = paginator.paginate_queryset(
                plans,
                request
            )

            serializer = SubscriptionPlanSerializer(
                paginated_plans,
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
            serializer = SubscriptionPlanSerializer(data=request.data)
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



# ------------------ Subscription Plan ------------------

class SubscriptionPlanDetailView(APIView):
    def get(self, request, pk):
        try:
            plan = get_object_or_404(SubscriptionPlan, pk=pk)
            serializer = SubscriptionPlanSerializer(plan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            plan = get_object_or_404(SubscriptionPlan, pk=pk)
            serializer = SubscriptionPlanSerializer(plan, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            plan = get_object_or_404(SubscriptionPlan, pk=pk)
            plan.delete()
            return Response({"message": "Subscription Plan deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Subscription Plan Variant ------------------
# List and Create Plan Variants (e.g., Connect+ 45 days, Connect+ 90 days)





class SubscriptionPlanVariantListCreateView(APIView):

    def get(self, request):
        try:
            variants = (
                SubscriptionPlanVariant.objects
                .select_related("plan_id")
                .all()
                .order_by('-variant_id')
            )

            paginator = GlobalPagination()
            paginated_variants = paginator.paginate_queryset(
                variants,
                request
            )

            serializer = SubscriptionPlanVariantSerializer(
                paginated_variants,
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
            serializer = SubscriptionPlanVariantSerializer(data=request.data)
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



class SubscriptionPlanVariantDetailView(APIView):
    def get(self, request, pk):
        try:
            variant = get_object_or_404(SubscriptionPlanVariant, pk=pk)
            serializer = SubscriptionPlanVariantSerializer(variant)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            variant = get_object_or_404(SubscriptionPlanVariant, pk=pk)
            serializer = SubscriptionPlanVariantSerializer(variant, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            variant = get_object_or_404(SubscriptionPlanVariant, pk=pk)
            variant.delete()
            return Response({"message": "Subscription Plan Variant deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


# ------------------ Subscription ------------------
# Create Subscription for User

class SubscriptionListCreateView(APIView):
    def get(self, request):
        try:
            subscriptions = Subscription.objects.all()
            serializer = SubscriptionSerializer(subscriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    


class SubscriptionDetailView(APIView):
    def get(self, request, subscription_id):
        try:
            subscription = get_object_or_404(Subscription,subscription_id=subscription_id)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request,subscription_id):
        try:
            subscription = get_object_or_404(Subscription, subscription_id=subscription_id)
            serializer = SubscriptionSerializer(subscription, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request,subscription_id):
        try:
            subscription = get_object_or_404(Subscription, subscription_id=subscription_id)
            subscription.delete()
            return Response({"message": "Subscription deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class UserSubscriptionsView(APIView):
    """
    GET → List user subscriptions (paginated) + latest_status
    """

    def get(self, request, user_id):
        try:
            subscriptions_qs = (
                Subscription.objects
                .filter(user_id=user_id)
                .order_by('-subscription_id')
            )

            # 🔹 Latest status (from most recent subscription)
            latest_status = (
                subscriptions_qs.first().subscription_status
                if subscriptions_qs.exists()
                else None
            )

            paginator = GlobalPagination()
            paginated_subscriptions = paginator.paginate_queryset(
                subscriptions_qs,
                request
            )

            serializer = SubscriptionSerializer(
                paginated_subscriptions,
                many=True
            )

            # Standard paginated response
            response = paginator.get_paginated_response(serializer.data)

            # 🔹 Add latest_status at top-level (BEST PRACTICE)
            response.data['latest_status'] = latest_status

            return response

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Get Subscription Plans based on user_type


class SubscriptionPlanByUserTypeView(APIView):
    """
    GET → List subscription plans by user_type (paginated)
    """

    def get(self, request, user_type):
        try:
            plans = (
                SubscriptionPlan.objects
                .filter(user_type=user_type)
                .order_by('-plan_id')
            )

            paginator = GlobalPagination()
            paginated_plans = paginator.paginate_queryset(
                plans,
                request
            )

            serializer = SubscriptionPlanSerializer(
                paginated_plans,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Get Subscription Plan Variants based on user_type



class SubscriptionPlanVariantByUserTypeView(APIView):
    """
    GET → List subscription plan variants by user_type (paginated)
    """

    def get(self, request, user_type):
        try:
            variants = (
                SubscriptionPlanVariant.objects
                .select_related("plan_id")
                .filter(plan_id__user_type=user_type)
                .order_by('-variant_id')
            )

            paginator = GlobalPagination()
            paginated_variants = paginator.paginate_queryset(
                variants,
                request
            )

            serializer = SubscriptionPlanVariantSerializer(
                paginated_variants,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class SubscriptionSearchAPIView(APIView):
    pagination_class = GlobalPagination

    def get(self, request):
        queryset = Subscription.objects.select_related(
            "user_id",
            "subscription_variant",
            "subscription_variant__plan_id"
        )

        # ---------------------------------------
        # FILTERS (including search)
        # ---------------------------------------
        filterset = SubscriptionFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        queryset = filterset.qs

        # ---------------------------------------
        # ORDERING
        # ---------------------------------------
        ordering = request.GET.get("ordering", "-subscription_id")

        allowed_ordering = [
            "subscription_id", "-subscription_id",
            "subscription_start_date", "-subscription_start_date",
            "subscription_end_date", "-subscription_end_date",
        ]

        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        # ---------------------------------------
        # PAGINATION
        # ---------------------------------------
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = SubscriptionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SubscriptionAnalyticsAPIView(APIView):

    def get(self, request):
        queryset = Subscription.objects.select_related(
            "user_id",
            "subscription_variant",
            "subscription_variant__plan_id"
        )

        # -------------------------------------------------
        # APPLY ALL FILTER COMBINATIONS (VERY IMPORTANT)
        # -------------------------------------------------
        filterset = SubscriptionFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        queryset = filterset.qs

        # -------------------------------------------------
        # PERIOD TYPE (monthly / weekly / yearly)
        # -------------------------------------------------
        period = request.GET.get("period", "monthly").lower()

        if period == "weekly":
            trunc_func = TruncWeek("subscription_start_date")
        elif period == "yearly":
            trunc_func = TruncYear("subscription_start_date")
        else:
            trunc_func = TruncMonth("subscription_start_date")

        # -------------------------------------------------
        # AGGREGATION
        # -------------------------------------------------
        analytics_qs = (
            queryset
            .annotate(period=trunc_func)
            .values("period")
            .annotate(
                total=Count("subscription_id"),
                active=Count(
                    "subscription_id",
                    filter=models.Q(subscription_end_date__gte=timezone.now().date())
                ),
                expired=Count(
                    "subscription_id",
                    filter=models.Q(subscription_end_date__lt=timezone.now().date())
                )
            )
            .order_by("period")
        )

        # -------------------------------------------------
        # FORMAT RESPONSE (FRONTEND FRIENDLY)
        # -------------------------------------------------
        data = []
        for row in analytics_qs:
            data.append({
                "period": row["period"],
                "total_subscriptions": row["total"],
                "active_subscriptions": row["active"],
                "expired_subscriptions": row["expired"],
            })

        return Response({
            "period_type": period,
            "filters_applied": request.GET,
            "results": data
        }, status=status.HTTP_200_OK)
