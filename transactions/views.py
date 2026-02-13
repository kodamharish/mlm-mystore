from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction as db_transaction
from .serializers import TransactionSerializer
from users.models import *
from property.models import *
from property.serializers import *
from mlm.pagination import GlobalPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Transaction
from .filters import *
from django.db.models import Sum, Count, Avg, Q


class TransactionDetailView(APIView):
    def get(self, request, transaction_id):
        try:
            transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, transaction_id):
        try:
            transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
            serializer = TransactionSerializer(transaction, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, transaction_id):
        try:
            transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
            transaction.delete()
            return Response({"message": "Transaction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class TransactionListCreateView(APIView):
    def get(self, request):
        try:
            queryset = (
                Transaction.objects
                .select_related("user_id", "property_id", "order")
                .prefetch_related("user_id__roles")
                .order_by("-transaction_date")
            )

            filterset = TransactionFilter(request.GET, queryset=queryset)

            if not filterset.is_valid():
                return Response(
                    filterset.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            filtered_queryset = filterset.qs.distinct()  # 🔥 IMPORTANT

            paginator = GlobalPagination()
            paginated_queryset = paginator.paginate_queryset(
                filtered_queryset,
                request
            )

            serializer = TransactionSerializer(
                paginated_queryset,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )










class TransactionsGroupedByPaymentTypeAPIView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Step 1: Fetch all UserProperty records for the user
        user_properties = UserProperty.objects.filter(user=user)

        # Step 2: Separate into booked and purchased
        booked_props = user_properties.filter(status='booked')
        purchased_props = user_properties.filter(status='sold')

        # Step 3: Get property objects
        booked_property_ids = booked_props.values_list('property_id', flat=True)
        purchased_property_ids = purchased_props.values_list('property_id', flat=True)

        booked_properties = Property.objects.filter(property_id__in=booked_property_ids)
        purchased_properties = Property.objects.filter(property_id__in=purchased_property_ids)

        # Step 4: Get transactions for the user
        transactions = Transaction.objects.filter(user_id=user)

        # Group transactions by type
        booking_transactions = transactions.filter(payment_type='Booking-Amount')
        full_transactions = transactions.filter(payment_type='Full-Amount')

        # Step 5: Serialize everything
        booking_transactions_serialized = TransactionSerializer(booking_transactions, many=True)
        full_transactions_serialized = TransactionSerializer(full_transactions, many=True)
        booked_properties_serialized = PropertySerializer(booked_properties, many=True)
        purchased_properties_serialized = PropertySerializer(purchased_properties, many=True)

        # Step 6: Payment breakdown per property
        property_ids = transactions.values_list('property_id', flat=True).distinct()
        breakdown = []

        for prop_id in property_ids:
            booking_total = transactions.filter(property_id=prop_id, payment_type='Booking-Amount').aggregate(
                total=Sum('paid_amount'))['total'] or 0
            full_total = transactions.filter(property_id=prop_id, payment_type='Full-Amount').aggregate(
                total=Sum('paid_amount'))['total'] or 0
            breakdown.append({
                "property_id": prop_id,
                "total_booking_amount_paid": booking_total,
                "total_full_amount_paid": full_total,
                "total_paid_amount": booking_total + full_total
            })

        return Response({
            "bookings": {
                "properties": {
                    "count": booked_properties.count(),
                    "list": booked_properties_serialized.data
                },
                "transactions": {
                    "count": booking_transactions.count(),
                    "list": booking_transactions_serialized.data
                }
            },
            "purchased": {
                "properties": {
                    "count": purchased_properties.count(),
                    "list": purchased_properties_serialized.data
                },
                "transactions": {
                    "count": full_transactions.count(),
                    "list": full_transactions_serialized.data
                }
            },
            "payment_breakdown": breakdown,
        }, status=status.HTTP_200_OK)


class AgentCommissionTransactionAPIView(APIView):
    def post(self, request):
        try:
            data = request.data

            # Required fields
            property_id = data.get('property_id')
            user_id = data.get('user_id')
            paid_amount = data.get('paid_amount')
            payment_mode = data.get('payment_mode')
           

            if not all([property_id, user_id, paid_amount, payment_mode]):
                return Response({
                    'error': 'property_id, user_id, paid_amount, and payment_mode are required.'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                prop = Property.objects.get(pk=property_id)
                user = User.objects.get(pk=user_id)
            except (Property.DoesNotExist, User.DoesNotExist):
                return Response({'error': 'Invalid property_id or user_id.'}, status=status.HTTP_404_NOT_FOUND)

            # Convert paid_amount to Decimal
            paid_amount = Decimal(str(paid_amount))

            # Create transaction record
            transaction = Transaction.objects.create(
                user_id=user,
                property_id=prop,
                transaction_for='property',
                payment_type='Agent-Commission',
                paid_amount=paid_amount,
                payment_mode=payment_mode,
                role='Agent',
                username=user.username,
                property_name=prop.property_title,
                property_value=prop.property_value,
                company_commission=prop.company_commission,
                
            )

            # Update commission totals
            total_paid = Transaction.objects.filter(
                property_id=prop,
                user_id=user,
                payment_type='Agent-Commission'
            ).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')

            prop.agent_commission_paid = total_paid
            prop.agent_commission_balance = (prop.agent_commission or Decimal('0.00')) - total_paid
            prop.save(update_fields=['agent_commission_paid', 'agent_commission_balance'])

            # Serialize and return transaction details
            serializer = TransactionSerializer(transaction)
            return Response({
                'message': 'Agent commission recorded successfully.',
                'transaction': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class OrderListAPIView(APIView):
    def get(self, request):
        try:
            queryset = (
                Order.objects
                .select_related("user")
                .order_by("-created_at")
            )

            filterset = OrderFilter(request.GET, queryset=queryset)

            if not filterset.is_valid():
                return Response(filterset.errors, status=400)

            #filtered_qs = filterset.qs
            filtered_qs = filterset.qs.distinct()

            paginator = GlobalPagination()
            paginated_qs = paginator.paginate_queryset(
                filtered_qs, request
            )

            serializer = OrderSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class OrderDetailAPIView(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=200)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)


class OrderItemListAPIView(APIView):
    def get(self, request):
        try:
            queryset = (
                OrderItem.objects
                .select_related("order", "variant", "property_item")
            )

            filterset = OrderItemFilter(request.GET, queryset=queryset)

            if not filterset.is_valid():
                return Response(filterset.errors, status=400)

            filtered_qs = filterset.qs

            paginator = GlobalPagination()
            paginated_qs = paginator.paginate_queryset(
                filtered_qs, request
            )

            serializer = OrderItemSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)




class OrderWithItemsAPIView(APIView):
    def get(self, request):
        try:
            queryset = (
                Order.objects
                .select_related("user")
                .prefetch_related(
                    "items",
                    "items__variant",
                    "items__property_item"
                )
                .order_by("-created_at")
            )

            # optional user filter
            user_id = request.GET.get("user_id")
            if user_id:
                queryset = queryset.filter(user__user_id=user_id)

            paginator = GlobalPagination()
            paginated_qs = paginator.paginate_queryset(queryset, request)

            serializer = OrderWithItemsSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)



class UserOrderSummaryAPIView(APIView):
    def get(self, request, user_id):
        try:
            orders = Order.objects.filter(user__user_id=user_id)

            if not orders.exists():
                return Response(
                    {"message": "No orders found for this user"},
                    status=200
                )

            summary = orders.aggregate(
                total_orders=Count("order_id"),
                total_spent=Sum("total_amount"),
                average_order_value=Avg("total_amount"),
                paid_orders=Count(
                    "order_id",
                    filter=models.Q(status="paid")
                ),
                pending_orders=Count(
                    "order_id",
                    filter=models.Q(status="pending")
                ),
                cancelled_orders=Count(
                    "order_id",
                    filter=models.Q(status="cancelled")
                ),
            )

            recent_orders = orders.order_by("-created_at")[:5]
            recent_orders_data = OrderWithItemsSerializer(
                recent_orders, many=True
            ).data

            return Response({
                "user_id": user_id,
                "summary": {
                    "total_orders": summary["total_orders"],
                    "paid_orders": summary["paid_orders"],
                    "pending_orders": summary["pending_orders"],
                    "cancelled_orders": summary["cancelled_orders"],
                    "total_spent": summary["total_spent"] or 0,
                    "average_order_value": summary["average_order_value"] or 0,
                },
                "recent_orders": recent_orders_data
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)







class OrderSummaryAPIView(APIView):
    def get(self, request):
        try:
            user_id = request.GET.get("user_id")
            role = request.GET.get("role")
            payment_mode = request.GET.get("payment_mode")
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")

            orders = Order.objects.select_related("user").all()

            # 🔹 User filter
            if user_id:
                orders = orders.filter(user__user_id=user_id)

            # 🔹 Role-based filter (via User → Role)
            if role:
                orders = orders.filter(
                    user__roles__role_name__iexact=role
                )

            # 🔹 Date-wise filter
            if start_date:
                orders = orders.filter(created_at__date__gte=start_date)
            if end_date:
                orders = orders.filter(created_at__date__lte=end_date)

            orders = orders.distinct()

            if not orders.exists():
                return Response(
                    {"message": "No orders found"},
                    status=status.HTTP_200_OK
                )

            # 🔹 Core order summary
            summary = orders.aggregate(
                total_orders=Count("order_id"),
                total_spent=Sum("total_amount"),
                average_order_value=Avg("total_amount"),
                paid_orders=Count(
                    "order_id", filter=Q(status="paid")
                ),
                pending_orders=Count(
                    "order_id", filter=Q(status="pending")
                ),
                cancelled_orders=Count(
                    "order_id", filter=Q(status="cancelled")
                ),
            )

            # 🔹 Payment-mode summary (from Transaction)
            transactions = Transaction.objects.filter(
                order__in=orders,
                status="success"
            )

            if payment_mode:
                transactions = transactions.filter(
                    payment_mode__iexact=payment_mode
                )

            payment_summary = (
                transactions
                .values("payment_mode")
                .annotate(
                    total_paid=Sum("paid_amount"),
                    transactions_count=Count("transaction_id")
                )
            )

            # 🔹 Recent orders
            recent_orders = (
                orders
                .prefetch_related("items", "items__variant", "items__property_item")
                .order_by("-created_at")[:5]
            )

            return Response({
                "scope": "user" if user_id else "global",
                "filters": {
                    "user_id": user_id,
                    "role": role,
                    "payment_mode": payment_mode,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "order_summary": {
                    "total_orders": summary["total_orders"],
                    "paid_orders": summary["paid_orders"],
                    "pending_orders": summary["pending_orders"],
                    "cancelled_orders": summary["cancelled_orders"],
                    "total_spent": summary["total_spent"] or 0,
                    "average_order_value": summary["average_order_value"] or 0,
                },
                "payment_summary": list(payment_summary),
                "recent_orders": OrderWithItemsSerializer(
                    recent_orders, many=True
                ).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils.dateparse import parse_date
from django.utils import timezone

from users.models import User
from property.models import Property, UserProperty
from transactions.models import Transaction
from subscription.models import Subscription


class AdminSummaryAPIView_new4(APIView):

    def get(self, request):

        user_id = request.GET.get("user_id")
        role = request.GET.get("role")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # =============================
        # BASE QUERYSETS
        # =============================
        users = User.objects.all()
        properties = Property.objects.all()
        transactions = Transaction.objects.all()
        subscriptions = Subscription.objects.all()

        # =============================
        # DATE FILTERS
        # =============================
        if start_date and end_date:
            date_range = [parse_date(start_date), parse_date(end_date)]
            transactions = transactions.filter(transaction_date__date__range=date_range)
            subscriptions = subscriptions.filter(
                subscription_start_datetime__date__range=date_range
            )

        # =============================
        # USER FILTER
        # =============================
        if user_id:
            users = users.filter(user_id=user_id)
            properties = properties.filter(user_id=user_id)
            transactions = transactions.filter(user_id=user_id)
            subscriptions = subscriptions.filter(user_id=user_id)

        # =============================
        # ROLE FILTER (ADMIN ONLY)
        # =============================
        if role and not user_id:
            users = users.filter(roles__role_name__iexact=role)
            properties = properties.filter(user_id__roles__role_name__iexact=role)
            transactions = transactions.filter(user_id__roles__role_name__iexact=role)
            subscriptions = subscriptions.filter(user_id__roles__role_name__iexact=role)

        # =====================================================
        # 👤 USER SUMMARY (ADMIN ONLY)
        # =====================================================
        if not user_id:
            user_summary = {
                "total_users": users.count(),
                "active": users.filter(status="active").count(),
                "inactive": users.filter(status="inactive").count(),
                "role_wise": []
            }

            role_user_qs = (
                users.values("roles__role_name")
                .annotate(
                    count=Count("user_id"),
                    active=Count("user_id", filter=Q(status="active")),
                    inactive=Count("user_id", filter=Q(status="inactive")),
                )
            )

            for row in role_user_qs:
                if row["roles__role_name"]:
                    user_summary["role_wise"].append({
                        "role": row["roles__role_name"],
                        "count": row["count"],
                        "active": row["active"],
                        "inactive": row["inactive"],
                    })

        # =====================================================
        # 🏠 PROPERTY SUMMARY
        # =====================================================
        if user_id:
            # -------- SELLER VIEW (Added by user) --------
            added_properties = Property.objects.filter(user_id=user_id)

            # seller_summary = {
            #     "total_added": added_properties.count(),
            #     "available": added_properties.filter(status="available").count(),
            #     "booked": added_properties.filter(status="booked").count(),
            #     "sold": added_properties.filter(status="sold").count(),
            # }

            seller_summary = {
                "total_added": added_properties.count(),

                # Status-wise (business flow)
                "available": added_properties.filter(status="available").count(),
                "booked": added_properties.filter(status="booked").count(),
                "sold": added_properties.filter(status="sold").count(),

                # Verification-wise (admin flow)
                "pending": added_properties.filter(verification_status="pending").count(),
                "verified": added_properties.filter(verification_status="verified").count(),
                "rejected": added_properties.filter(verification_status="rejected").count(),
            }


            # -------- BUYER VIEW (Booked / Purchased by user) --------
            user_properties = UserProperty.objects.filter(user_id=user_id)

            buyer_summary = {
                "booked": user_properties.filter(status="booked").count(),
                "purchased": user_properties.filter(status="purchased").count(),
            }

            property_summary = {
                "seller": seller_summary,
                "buyer": buyer_summary
            }

        else:
            # -------- ADMIN GLOBAL VIEW --------
            property_summary = {
                "total_properties": properties.count(),
                "pending": properties.filter(verification_status="pending").count(),
                "verified": properties.filter(verification_status="verified").count(),
                "available": properties.filter(status="available").count(),
                "booked": properties.filter(status="booked").count(),
                "sold": properties.filter(status="sold").count(),
                "rejected": properties.filter(verification_status="rejected").count(),
                "role_wise": []
            }

            role_property_qs = (
                Property.objects
                .values("user_id__roles__role_name")
                .annotate(
                    total_properties=Count("property_id"),
                    verified=Count("property_id", filter=Q(verification_status="verified")),
                    pending=Count("property_id", filter=Q(verification_status="pending")),
                    sold=Count("property_id", filter=Q(status="sold")),
                )
            )

            for row in role_property_qs:
                if row["user_id__roles__role_name"]:
                    property_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "total_properties": row["total_properties"],
                        "verified": row["verified"],
                        "pending": row["pending"],
                        "sold": row["sold"],
                    })

        # =====================================================
        # 💳 TRANSACTION SUMMARY
        # =====================================================
        transaction_summary = {
            "total_transactions": transactions.count(),
            "success": transactions.filter(status="success").count(),
            "failed": transactions.filter(status="failed").count(),
            "refunded": transactions.filter(status="refunded").count(),
            "total_revenue": transactions.filter(status="success")
                .aggregate(amount=Sum("paid_amount"))["amount"] or 0,
        }

        if not user_id:
            transaction_summary["role_wise"] = []

            role_transaction_qs = (
                Transaction.objects
                .filter(status="success")
                .values("user_id__roles__role_name")
                .annotate(
                    count=Count("transaction_id"),
                    amount=Sum("paid_amount")
                )
            )

            for row in role_transaction_qs:
                if row["user_id__roles__role_name"]:
                    transaction_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "count": row["count"],
                        "amount": row["amount"] or 0,
                    })

        # =====================================================
        # 📦 SUBSCRIPTION SUMMARY
        # =====================================================
        now = timezone.now()

        subscription_summary = {
            "total_subscriptions": subscriptions.count(),
            "active": subscriptions.filter(subscription_end_datetime__gte=now).count(),
            "expired": subscriptions.filter(subscription_end_datetime__lt=now).count(),
            "subscription_revenue": Transaction.objects.filter(
                transaction_for="subscription",
                status="success"
            ).aggregate(amount=Sum("paid_amount"))["amount"] or 0,
        }

        if not user_id:
            subscription_summary["role_wise"] = []

            role_subscription_qs = (
                Subscription.objects
                .values("user_id__roles__role_name")
                .annotate(count=Count("subscription_id"))
            )

            for row in role_subscription_qs:
                if row["user_id__roles__role_name"]:
                    subscription_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "count": row["count"]
                    })

        # =====================================================
        # FINAL RESPONSE
        # =====================================================
        response = {
            "filters_applied": {
                "user_id": user_id,
                "role": role,
                "start_date": start_date,
                "end_date": end_date,
            },
            "property_summary": property_summary,
            "transaction_summary": transaction_summary,
            "subscription_summary": subscription_summary,
        }

        if not user_id:
            response["user_summary"] = user_summary

        return Response(response)






class AdminSummaryAPIView(APIView):

    def get(self, request):

        user_id = request.GET.get("user_id")
        role = request.GET.get("role")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # =============================
        # BASE QUERYSETS
        # =============================
        users = User.objects.all()
        properties = Property.objects.all()
        transactions = Transaction.objects.all()
        orders = Order.objects.all()
        subscriptions = Subscription.objects.all()

        # =============================
        # DATE FILTERS (apply where relevant)
        # =============================
        if start_date and end_date:
            date_range = [parse_date(start_date), parse_date(end_date)]
            transactions = transactions.filter(transaction_date__date__range=date_range)
            orders = orders.filter(created_at__date__range=date_range)
            subscriptions = subscriptions.filter(subscription_start_datetime__date__range=date_range)

        # =============================
        # USER FILTER
        # =============================
        if user_id:
            users = users.filter(user_id=user_id)
            properties = properties.filter(user_id=user_id)
            transactions = transactions.filter(user_id=user_id)
            orders = orders.filter(user_id=user_id)
            subscriptions = subscriptions.filter(user_id=user_id)

        # =============================
        # ROLE FILTER (ADMIN ONLY)
        # =============================
        if role and not user_id:
            users = users.filter(roles__role_name__iexact=role)
            properties = properties.filter(user_id__roles__role_name__iexact=role)
            transactions = transactions.filter(user_id__roles__role_name__iexact=role)
            orders = orders.filter(user__roles__role_name__iexact=role)
            subscriptions = subscriptions.filter(user_id__roles__role_name__iexact=role)

        # =====================================================
        # 👤 USER SUMMARY (ADMIN ONLY)
        # =====================================================
        if not user_id:
            user_summary = {
                "total_users": users.count(),
                "active": users.filter(status="active").count(),
                "inactive": users.filter(status="inactive").count(),
                "role_wise": []
            }

            role_user_qs = (
                users.values("roles__role_name")
                .annotate(
                    count=Count("user_id"),
                    active=Count("user_id", filter=Q(status="active")),
                    inactive=Count("user_id", filter=Q(status="inactive")),
                )
            )

            for row in role_user_qs:
                if row["roles__role_name"]:
                    user_summary["role_wise"].append({
                        "role": row["roles__role_name"],
                        "count": row["count"],
                        "active": row["active"],
                        "inactive": row["inactive"],
                    })

        # =====================================================
        # 🏠 PROPERTY SUMMARY
        # =====================================================
        if user_id:
            # -------- SELLER: My Properties (added by me) --------
            added_properties = Property.objects.filter(user_id=user_id)

            my_properties = {
                "total_added": added_properties.count(),
                "available": added_properties.filter(status="available").count(),
                "booked": added_properties.filter(status="booked").count(),
                "sold": added_properties.filter(status="sold").count(),
                "pending": added_properties.filter(verification_status="pending").count(),
                "verified": added_properties.filter(verification_status="verified").count(),
                "rejected": added_properties.filter(verification_status="rejected").count(),
            }

            # -------- BUYER: Bookings & Purchases --------
            user_properties = UserProperty.objects.filter(user_id=user_id)

            bookings = {
                "count": user_properties.filter(status="booked").count()
            }

            buyied_or_purchased = {
                "count": user_properties.filter(status="purchased").count()
            }

            property_summary = {
                "my_properties": my_properties,
                "bookings": bookings,
                "buyied_or_purchased": buyied_or_purchased
            }

        else:
            # -------- ADMIN GLOBAL VIEW --------
            property_summary = {
                "total_properties": properties.count(),
                "pending": properties.filter(verification_status="pending").count(),
                "verified": properties.filter(verification_status="verified").count(),
                "available": properties.filter(status="available").count(),
                "booked": properties.filter(status="booked").count(),
                "sold": properties.filter(status="sold").count(),
                "rejected": properties.filter(verification_status="rejected").count(),
                "role_wise": []
            }

            role_property_qs = (
                Property.objects
                .values("user_id__roles__role_name")
                .annotate(
                    total_properties=Count("property_id"),
                    verified=Count("property_id", filter=Q(verification_status="verified")),
                    pending=Count("property_id", filter=Q(verification_status="pending")),
                    sold=Count("property_id", filter=Q(status="sold")),
                )
            )

            for row in role_property_qs:
                if row["user_id__roles__role_name"]:
                    property_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "total_properties": row["total_properties"],
                        "verified": row["verified"],
                        "pending": row["pending"],
                        "sold": row["sold"],
                    })

        # =====================================================
        # 💳 TRANSACTION SUMMARY
        # =====================================================
        transaction_summary = {
            "total_transactions": transactions.count(),
            "success": transactions.filter(status="success").count(),
            "failed": transactions.filter(status="failed").count(),
            "refunded": transactions.filter(status="refunded").count(),
            "total_revenue": transactions.filter(status="success")
                .aggregate(amount=Sum("paid_amount"))["amount"] or 0,
        }

        if not user_id:
            transaction_summary["role_wise"] = []

            role_transaction_qs = (
                Transaction.objects
                .filter(status="success")
                .values("user_id__roles__role_name")
                .annotate(
                    count=Count("transaction_id"),
                    amount=Sum("paid_amount")
                )
            )

            for row in role_transaction_qs:
                if row["user_id__roles__role_name"]:
                    transaction_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "count": row["count"],
                        "amount": row["amount"] or 0,
                    })

        # =====================================================
        # 🧾 ORDER SUMMARY
        # =====================================================
        order_summary = {
            "total_orders": orders.count(),
            "paid": orders.filter(status="paid").count(),
            "pending": orders.filter(status="pending").count(),
            "cancelled": orders.filter(status="cancelled").count(),
            "refunded": orders.filter(status="refunded").count(),
        }

        if not user_id:
            order_summary["role_wise"] = []

            role_order_qs = (
                Order.objects
                .values("user__roles__role_name")
                .annotate(count=Count("order_id"))
            )

            for row in role_order_qs:
                if row["user__roles__role_name"]:
                    order_summary["role_wise"].append({
                        "role": row["user__roles__role_name"],
                        "count": row["count"],
                    })

        # =====================================================
        # 📦 SUBSCRIPTION SUMMARY
        # =====================================================
        now = timezone.now()

        subscription_summary = {
            "total_subscriptions": subscriptions.count(),
            "active": subscriptions.filter(subscription_end_datetime__gte=now).count(),
            "expired": subscriptions.filter(subscription_end_datetime__lt=now).count(),
            "subscription_revenue": Transaction.objects.filter(
                transaction_for="subscription",
                status="success"
            ).aggregate(amount=Sum("paid_amount"))["amount"] or 0,
        }

        if not user_id:
            subscription_summary["role_wise"] = []

            role_subscription_qs = (
                Subscription.objects
                .values("user_id__roles__role_name")
                .annotate(count=Count("subscription_id"))
            )

            for row in role_subscription_qs:
                if row["user_id__roles__role_name"]:
                    subscription_summary["role_wise"].append({
                        "role": row["user_id__roles__role_name"],
                        "count": row["count"]
                    })

        # =====================================================
        # FINAL RESPONSE
        # =====================================================
        response = {
            "filters_applied": {
                "user_id": user_id,
                "role": role,
                "start_date": start_date,
                "end_date": end_date,
            },
            "property_summary": property_summary,
            "transaction_summary": transaction_summary,
            "order_summary": order_summary,
            "subscription_summary": subscription_summary,
        }

        if not user_id:
            response["user_summary"] = user_summary

        return Response(response)
