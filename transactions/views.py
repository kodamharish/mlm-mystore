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
from django.db.models import Sum, Q
from property.serializers import *




class TransactionListCreateView(APIView):
    def get(self, request):
        try:
            transactions = Transaction.objects.all().order_by("-transaction_date")
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @db_transaction.atomic
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")

            # Validate user
            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Validate property
            property_obj = Property.objects.filter(property_id=property_id).first()
            if not property_obj:
                return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

            # Determine booking or purchase based on payment_type
            if payment_type == "Booking-Amount":
                new_status = "booked"
                date_field = "booking_date"
            elif payment_type == "Full-Amount":
                new_status = "purchased"
                date_field = "purchase_date"
            else:
                return Response({"error": "Invalid payment_type. Allowed: Booking-Amount or Full-Amount"}, status=status.HTTP_400_BAD_REQUEST)

            # Prevent duplicate booking/purchase by same user for this property and status
            if UserProperty.objects.filter(user=user, property=property_obj, status=new_status).exists():
                return Response({"error": f"Property already {new_status} by this user"}, status=status.HTTP_400_BAD_REQUEST)

            # Prevent booking if property already purchased
            if new_status == "booked" and property_obj.status == "purchased":
                return Response({"error": "Property already purchased and cannot be booked"}, status=status.HTTP_400_BAD_REQUEST)

            # Prevent purchase if property already purchased
            if new_status == "purchased" and property_obj.status == "purchased":
                return Response({"error": "Property already purchased"}, status=status.HTTP_400_BAD_REQUEST)

            # Save Transaction
            serializer = TransactionSerializer(data=request.data,context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            transaction_instance = serializer.save()

            # Create or update UserProperty
            user_property, created = UserProperty.objects.get_or_create(
                user=user,
                property=property_obj,
                defaults={ "status": new_status, date_field: timezone.now().date() }
            )
            if not created:
                # Upgrade booking to purchase if applicable
                if new_status == "purchased" and user_property.status != "purchased":
                    user_property.status = "purchased"
                    setattr(user_property, date_field, timezone.now().date())
                    user_property.save()

            # Update Property status if needed
            if new_status == "purchased":
                property_obj.status = "purchased"
                property_obj.save()
            elif new_status == "booked" and property_obj.status == "available":
                property_obj.status = "booked"
                property_obj.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


# Filter Views

class TransactionByPropertyId(APIView):
    def get(self, request, property_id):
        try:
            transactions = Transaction.objects.filter(property_id=property_id)
            if not transactions.exists():
                return Response({"error": "No transactions found for this property"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionByUserId(APIView):
    def get(self, request, user_id):
        try:
            transactions = Transaction.objects.filter(user_id=user_id)
            if not transactions.exists():
                return Response({"error": "No transactions found for this user"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PropertyOrSubcriptionTransactionByUserId(APIView):
    def get(self, request, user_id,transaction_for):
        try:
            transactions = Transaction.objects.filter(user_id=user_id,transaction_for=transaction_for)
            if not transactions.exists():
                return Response({"error": "No transactions found for this user"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class PropertyOrSubcriptionTransactions(APIView):
    def get(self, request,transaction_for):
        try:
            transactions = Transaction.objects.filter(transaction_for=transaction_for)
            if not transactions.exists():
                return Response({"error": "No transactions found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

class TransactionByUserIdAndPropertyId(APIView):
    def get(self, request, user_id, property_id):
        try:
            transactions = Transaction.objects.filter(user_id=user_id, property_id=property_id)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user and property id"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionByUserIdAndPaymentType(APIView):
    def get(self, request, user_id, payment_type):
        try:
            transactions = Transaction.objects.filter(user_id=user_id, payment_type=payment_type)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user and payment type"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionByUserIdPropertyIdAndPaymentType(APIView):
    def get(self, request, user_id, property_id, payment_type):
        try:
            transactions = Transaction.objects.filter(user_id=user_id, property_id=property_id, payment_type=payment_type)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user, property, and payment type"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionByPropertyIdAndPaymentType(APIView):
    def get(self, request, property_id, payment_type):
        try:
            transactions = Transaction.objects.filter(property_id=property_id, payment_type=payment_type)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user, property, and payment type"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class TransactionByPaymentType(APIView):
    def get(self, request, payment_type):
        try:
            transactions = Transaction.objects.filter(payment_type=payment_type)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user and payment type"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class TransactionByUserRolePaymentType(APIView):
    def get(self, request,role, payment_type):
        try:
            transactions = Transaction.objects.filter(role=role,payment_type=payment_type)
            if not transactions.exists():
                return Response({"error": "No transactions found for the given user and payment type"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class TransactionsGroupedByPaymentTypeAPIView_old(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Step 1: Fetch all UserProperty records for the user
        user_properties = UserProperty.objects.filter(user=user)

        # Step 2: Separate into booked and purchased
        booked_props = user_properties.filter(status='booked')
        purchased_props = user_properties.filter(status='purchased')

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


class UserOrderListAPIView(APIView):
    def get(self, request, user_id):
        try:
            orders = Order.objects.filter(user_id=user_id).order_by("-created_at")
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class OrderItemByOrderAPIView(APIView):
    def get(self, request, order_id):
        try:
            items = OrderItem.objects.filter(order_id=order_id)
            serializer = OrderItemSerializer(items, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class OrderListAPIView(APIView):
    def get(self, request):
        try:
            orders = Order.objects.all().order_by("-created_at")
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)



class OrderItemListAPIView(APIView):
    def get(self, request):
        try:
            items = OrderItem.objects.select_related("order", "product")
            serializer = OrderItemSerializer(items, many=True)
            return Response(serializer.data, status=200)
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
