from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from subscription.models import SubscriptionPlanVariant
from users.models import User
from .utils import *  
from subscription.models import *
from transactions.models import *
from users.models import *
import os
from datetime import date
from django.utils import timezone
from io import BytesIO
from datetime import datetime
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction as db_transaction
from reportlab.pdfgen import canvas




class SubscriptionInitiatePaymentAPIView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            variant_id = request.data.get("variant_id")
            redirect_url = request.data.get("redirect_url")

            if not all([user_id, variant_id, redirect_url]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            variant = SubscriptionPlanVariant.objects.get(variant_id=variant_id)

            amount = int(variant.price * 100)  # PhonePe expects paise

            # STEP 1: Initiate payment with PhonePe
            result = initiate_payment(amount=amount, redirect_url=redirect_url)

            merchant_order_id = result.get("merchant_order_id")

            if not merchant_order_id:
                return Response({"error": "Failed to initiate payment"}, status=500)

            # STEP 2: Create pending Transaction (like Product flow)
            txn = Transaction.objects.create(
                user_id=user,
                transaction_for="subscription",
                paid_amount=variant.price,
                status="pending",
                subscription_variant=variant,
                plan_name=variant.plan_id.plan_name,
                phone_pe_merchant_order_id=merchant_order_id
            )

            return Response({
                "transaction_id": txn.transaction_id,
                "merchant_order_id": merchant_order_id,
                "payment_url": result["redirect_url"],
                "amount": variant.price
            }, status=200)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except SubscriptionPlanVariant.DoesNotExist:
            return Response({"error": "Subscription plan not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)




class PropertyInitiatePaymentAPIView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")
            redirect_url = request.data.get("redirect_url")

            if not all([user_id, property_id, payment_type, redirect_url]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            property_obj = Property.objects.get(property_id=property_id)

            if payment_type == "Booking-Amount":
                amount = int(property_obj.booking_amount * 100)
            elif payment_type == "Full-Amount":
                amount = int(property_obj.property_value_without_booking_amount * 100)
            else:
                return Response({"error": "Invalid payment_type. Use 'Booking-Amount' or 'Full-Amount'"}, status=400)

            result = initiate_payment(amount=amount, redirect_url=redirect_url)

            return Response({
                "merchant_order_id": result["merchant_order_id"],
                "payment_url": result["redirect_url"]
            }, status=200)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)









class PropertyInitiatePaymentAPIView_new1(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")
            redirect_url = request.data.get("redirect_url")

            if not all([user_id, property_id, payment_type]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            property_obj = Property.objects.get(property_id=property_id)

            # ---------------------------
            # CASE 1: Booking-Amount → Online (PhonePe)
            # ---------------------------
            if payment_type == "Booking-Amount":
                if not redirect_url:
                    return Response({"error": "redirect_url is required for online payment"}, status=400)

                amount = int(property_obj.booking_amount * 100)
                result = initiate_payment(amount=amount, redirect_url=redirect_url)

                return Response({
                    "payment_type": "Booking-Amount",
                    "merchant_order_id": result["merchant_order_id"],
                    "payment_url": result["redirect_url"],
                    "message": "Redirect to PhonePe for booking payment"
                }, status=200)

            # ---------------------------
            # CASE 2: Full-Amount → Manual (Cash)
            # ---------------------------
            elif payment_type == "Full-Amount":
                # No PhonePe API call
                total_amount = float(property_obj.property_value_without_booking_amount)
                return Response({
                    "payment_type": "Full-Amount",
                    "payment_mode": "Manual (Cash)",
                    "total_amount": total_amount,
                    "message": f"Manual cash payment required of ₹{total_amount} for Full-Amount purchase."
                }, status=200)

            # ---------------------------
            # Invalid type
            # ---------------------------
            else:
                return Response({
                    "error": "Invalid payment_type. Use 'Booking-Amount' or 'Full-Amount'"
                }, status=400)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)





def generate_transaction_doc_number():
    # Get the highest numeric part from existing invoice numbers
    last_invoice = (
        Transaction.objects
        .filter(document_number__startswith='INV')
        .order_by('-transaction_id')      # or '-doc_number' if id isn’t guaranteed sequential
        .first()
    )

    if last_invoice and last_invoice.document_number:
        # Extract digits after 'INV' and convert to int
        try:
            last_number = int(last_invoice.document_number.replace('INV', ''))
        except ValueError:
            last_number = 0
    else:
        last_number = 0

    next_number = last_number + 1
    return f"INV{next_number}"





class SubscriptionConfirmPaymentAPIView(APIView):
    def post(self, request):
        try:
            merchant_order_id = request.data.get("merchant_order_id")

            if not merchant_order_id:
                return Response({"error": "merchant_order_id required"}, status=400)

            # STEP 1: Check payment status from PhonePe
            payment_status_data = check_payment_status(merchant_order_id)

            if payment_status_data.get("status") != "COMPLETED":
                return Response(
                    {**payment_status_data, "message": "Payment not completed"},
                    status=202
                )

            with db_transaction.atomic():

                # STEP 2: Lock and fetch pending transaction
                txn = Transaction.objects.select_for_update().get(
                    phone_pe_merchant_order_id=merchant_order_id,
                    status="pending"
                )

                user = txn.user_id
                variant = txn.subscription_variant

                # STEP 3: Extract payment details
                payment_details = payment_status_data.get("payment_details", [])
                phone_pe_transaction_id = (
                    payment_details[0]["transaction_id"] if payment_details else None
                )
                payment_mode_from_response = (
                    payment_details[0]["payment_mode"] if payment_details else None
                )

                # STEP 4: Generate document number
                doc_number = generate_transaction_doc_number()

                # STEP 5: Update transaction (instead of creating new)
                txn.phone_pe_transaction_id = phone_pe_transaction_id
                txn.phone_pe_order_id = payment_status_data.get("order_id")
                txn.payment_mode = payment_mode_from_response
                txn.status = "success"
                txn.document_number = doc_number
                txn.save(update_fields=[
                    "phone_pe_transaction_id",
                    "phone_pe_order_id",
                    "payment_mode",
                    "status",
                    "document_number"
                ])

                # STEP 6: Create subscription
                Subscription.objects.create(
                    user_id=user,
                    subscription_variant=variant,
                    subscription_status="paid"
                )

                # Activate user
                user.status = "active"
                user.save(update_fields=["status"])

            # STEP 7: Generate invoice PDF
            generate_subscription_invoice_pdf(txn, user, variant, doc_number)

            return Response({
                "message": "Payment verified, subscription created, and invoice generated successfully",
                **payment_status_data
            }, status=201)

        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found or already processed"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class PropertyConfirmPaymentAPIView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")  # 'Full-Amount' or 'Booking-Amount'
            merchant_order_id = request.data.get("merchant_order_id")
            doc_file = request.FILES.get("document_file")
            # 🔥 CRITICAL FIX: Check for duplicate transaction first
            existing_transaction = Transaction.objects.filter(
                phone_pe_merchant_order_id=merchant_order_id,
                payment_type=payment_type,
                property_id=property_id
            ).first()
            
            if existing_transaction:
                return Response({
                    "message": "Transaction already processed",
                    "transaction_id": existing_transaction.id,
                    "document_number": existing_transaction.document_number
                }, status=200)  # Return 200 instead of error

            if not all([user_id, property_id, payment_type, merchant_order_id]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            property_obj = Property.objects.get(property_id=property_id)

            # Step 1: Check payment status
            payment_status_data = check_payment_status(merchant_order_id)
            payment_state = payment_status_data.get("status")

            if payment_state != "COMPLETED":
                return Response({
                    **payment_status_data,
                    "message": "Payment not completed"
                }, status=202)

            # Step 2: Extract payment details
            payment_details = payment_status_data.get("payment_details", [])
            phone_pe_transaction_id = payment_details[0]["transaction_id"] if payment_details else None
            payment_mode = payment_details[0]["payment_mode"] if payment_details else None

            # Step 3: Determine amounts and logic
            if payment_type == "Booking-Amount":
                new_status = "booked"
                paid_amount = property_obj.booking_amount
                remaining_amount = property_obj.property_value_without_booking_amount

                date_field = "booking_date"
                #doc_type = "receipt"
            elif payment_type == "Full-Amount":
                new_status = "purchased"
                paid_amount = property_obj.property_value_without_booking_amount
                remaining_amount = 0.00
                date_field = "purchase_date"
                #doc_type = "invoice"
            else:
                return Response({"error": "Invalid payment_type"}, status=400)

            # Step 4: Generate document number and optionally rename file
            doc_number = generate_transaction_doc_number()

            if doc_file:
                ext = os.path.splitext(doc_file.name)[1]
                doc_file.name = f"{doc_number}{ext}"

            # Step 5: Check for duplicate transactions
            if UserProperty.objects.filter(user=user, property=property_obj, status=new_status).exists():
                return Response({"error": f"Property already {new_status} by this user"}, status=400)

            if property_obj.status == "sold":
                return Response({"error": "Property already sold"}, status=400)
            
            # Extract user roles
            user_roles = user.roles.all().values_list("role_name", flat=True)
            role_str = user_roles[0] if user_roles else None


            # Step 6: Create Transaction
            transaction = Transaction.objects.create(
                user_id=user,
                
                property_id=property_obj,
                property_name = property_obj.property_title,
                property_value = property_obj.total_property_value,
                remaining_amount = remaining_amount,
                company_commission = property_obj.company_commission,
                transaction_for="property",
                role=role_str,
                paid_amount=paid_amount,
                payment_mode=payment_mode,
                phone_pe_merchant_order_id=payment_status_data.get("merchant_order_id"),
                phone_pe_order_id=payment_status_data.get("order_id"),
                phone_pe_transaction_id=phone_pe_transaction_id,
                payment_type=payment_type,
                #document_type=doc_type,
                document_number=doc_number,
                document_file=doc_file,
            )

            #generate_invoice_pdf(transaction, user, property_obj, doc_number)

            # inside PropertyConfirmPaymentAPIView after creating `transaction`
            generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type)


            # Step 7: Create or update UserProperty
            user_property, created = UserProperty.objects.get_or_create(
                user=user,
                property=property_obj,
                defaults={"status": new_status, date_field: timezone.now().date()}
            )

            if not created and new_status == "purchased" and user_property.status != "purchased":
                user_property.status = "purchased"
                setattr(user_property, date_field, timezone.now().date())
                user_property.save()

            # Step 8: Update Property status
            if new_status == "purchased" and property_obj.status == "booked":
                property_obj.status = "sold"
            elif new_status == "booked" and property_obj.status == "available":
                property_obj.status = "booked"
            property_obj.save()

            return Response({
                "message": "Payment verified and transaction recorded successfully",
                **payment_status_data
            }, status=201)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)











class PropertyConfirmPaymentAPIView_new1(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")  # Booking-Amount | Full-Amount
            merchant_order_id = request.data.get("merchant_order_id")
            doc_file = request.FILES.get("document_file")

            # Manual cash fields
            cash_reference = request.data.get("cash_reference")
            cash_receipt = request.FILES.get("cash_receipt")

            if not all([user_id, property_id, payment_type]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            property_obj = Property.objects.get(property_id=property_id)

            # User role
            user_roles = user.roles.all().values_list("role_name", flat=True)
            role_str = user_roles[0] if user_roles else None

            # ---------------------------------------------------------
            # CASE 1: Booking Amount (PhonePe Online Payment)
            # ---------------------------------------------------------
            if payment_type == "Booking-Amount":
                if not merchant_order_id:
                    return Response({"error": "Missing merchant_order_id"}, status=400)

                # Step 1: Verify payment status
                payment_status_data = check_payment_status(merchant_order_id)
                payment_state = payment_status_data.get("status")

                if payment_state != "COMPLETED":
                    return Response({
                        "status": payment_state,
                        "message": "Payment not completed"
                    }, status=202)

                # Payment details
                payment_details = payment_status_data.get("payment_details", [])
                phone_pe_transaction_id = payment_details[0]["transaction_id"] if payment_details else None
                payment_mode = payment_details[0]["payment_mode"] if payment_details else None

                # ---------------------------------------------------------
                # FIX: Prevent duplicate PhonePe callbacks (IDEMPOTENCY)
                # ---------------------------------------------------------
                existing_txn = Transaction.objects.filter(
                    phone_pe_merchant_order_id=payment_status_data.get("merchant_order_id")
                ).first()

                if existing_txn:
                    return Response({
                        "message": "Duplicate callback ignored",
                        "transaction_id": existing_txn.transaction_id
                    }, status=200)

                # Step 2: Amount calculation
                new_status = "booked"
                paid_amount = property_obj.booking_amount
                remaining_amount = property_obj.property_value_without_booking_amount
                date_field = "booking_date"

                # Step 3: Prevent duplicate bookings
                if UserProperty.objects.filter(user=user, property=property_obj, status=new_status).exists():
                    return Response({"error": "Property already booked by this user"}, status=400)

                if property_obj.status == "sold":
                    return Response({"error": "Property already sold"}, status=400)

                # Step 4: Generate document number
                doc_number = generate_transaction_doc_number()
                if doc_file:
                    ext = os.path.splitext(doc_file.name)[1]
                    doc_file.name = f"{doc_number}{ext}"

                # ---------------------------------------------------------
                # Step 5: CREATE TRANSACTION (Only ONE allowed)
                # ---------------------------------------------------------
                transaction = Transaction.objects.create(
                    user_id=user,
                    property_id=property_obj,
                    property_name=property_obj.property_title,
                    property_value=property_obj.total_property_value,
                    remaining_amount=remaining_amount,
                    company_commission=property_obj.company_commission,
                    transaction_for="property",
                    role=role_str,
                    paid_amount=paid_amount,
                    payment_mode=payment_mode,
                    phone_pe_merchant_order_id=payment_status_data.get("merchant_order_id"),
                    phone_pe_order_id=payment_status_data.get("order_id"),
                    phone_pe_transaction_id=phone_pe_transaction_id,
                    payment_type=payment_type,
                    document_number=doc_number,
                    document_file=doc_file,
                )

                # Step 6: Generate invoice PDF
                generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type)

                # Step 7: Update UserProperty & Property
                user_property, created = UserProperty.objects.get_or_create(
                    user=user,
                    property=property_obj,
                    defaults={"status": new_status, date_field: timezone.now().date()}
                )

                if not created:
                    user_property.status = new_status
                    setattr(user_property, date_field, timezone.now().date())
                    user_property.save()

                if property_obj.status == "available":
                    property_obj.status = "booked"
                    property_obj.owner = user
                    property_obj.save()

                return Response({"message": "Booking payment confirmed"}, status=201)

            # ---------------------------------------------------------
            # CASE 2: Full Amount (Manual Cash Payment)
            # ---------------------------------------------------------
            elif payment_type == "Full-Amount":

                paid_amount = float(property_obj.property_value_without_booking_amount)

                # Step 1: Generate document number
                doc_number = generate_transaction_doc_number()
                if cash_receipt:
                    ext = os.path.splitext(cash_receipt.name)[1]
                    cash_receipt.name = f"{doc_number}{ext}"

                # Step 2: Prevent duplicates
                if UserProperty.objects.filter(user=user, property=property_obj, status="purchased").exists():
                    return Response({"error": "Already Purchased"}, status=400)

                if property_obj.status == "sold":
                    return Response({"error": "Property already sold"}, status=400)

                # Step 3: Create transaction
                transaction = Transaction.objects.create(
                    user_id=user,
                    
                    property_id=property_obj,
                    property_name=property_obj.property_title,
                    property_value=property_obj.total_property_value,
                    remaining_amount=0,
                    company_commission=property_obj.company_commission,
                    transaction_for="property",
                    role=role_str,
                    paid_amount=paid_amount,
                    payment_mode="Cash",
                    payment_type="Full-Amount",
                    document_number=doc_number,
                    document_file=cash_receipt,
                )

                # Step 4: Generate invoice
                generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type)

                # Step 5: Update user-property
                user_property, _ = UserProperty.objects.get_or_create(
                    user=user,
                    property=property_obj,
                    defaults={"status": "purchased", "purchase_date": timezone.now().date()}
                )
                user_property.status = "purchased"
                user_property.purchase_date = timezone.now().date()
                user_property.save()

                # Step 6: Update property status
                property_obj.status = "sold"
                property_obj.owner = user
                property_obj.save()

                return Response({"message": "Full payment processed"}, status=201)

            else:
                return Response({"error": "Invalid payment_type"}, status=400)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        







class PropertyConfirmPaymentAPIViewdonotcreateduplicatetransactions(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            property_id = request.data.get("property_id")
            payment_type = request.data.get("payment_type")  # Booking-Amount | Full-Amount
            merchant_order_id = request.data.get("merchant_order_id")
            doc_file = request.FILES.get("document_file")

            # Manual cash fields
            cash_reference = request.data.get("cash_reference")
            cash_receipt = request.FILES.get("cash_receipt")

            if not all([user_id, property_id, payment_type]):
                return Response({"error": "Missing required fields"}, status=400)

            user = User.objects.get(user_id=user_id)
            property_obj = Property.objects.get(property_id=property_id)

            # User role
            user_roles = user.roles.all().values_list("role_name", flat=True)
            role_str = user_roles[0] if user_roles else None

            # ---------------------------------------------------------
            # CASE 1: Booking Amount (PhonePe Online Payment)
            # ---------------------------------------------------------
            if payment_type == "Booking-Amount":
                if not merchant_order_id:
                    return Response({"error": "Missing merchant_order_id"}, status=400)

                # Step 1: Verify payment status
                payment_status_data = check_payment_status(merchant_order_id)
                payment_state = payment_status_data.get("status")

                if payment_state != "COMPLETED":
                    return Response({
                        "status": payment_state,
                        "message": "Payment not completed"
                    }, status=202)

                # Payment details
                payment_details = payment_status_data.get("payment_details", [])
                phone_pe_transaction_id = payment_details[0]["transaction_id"] if payment_details else None
                payment_mode = payment_details[0]["payment_mode"] if payment_details else None

                # ---------------------------------------------------------
                # FIX: Prevent duplicate PhonePe callbacks (IDEMPOTENCY)
                # ---------------------------------------------------------
                existing_txn = Transaction.objects.filter(
                    phone_pe_merchant_order_id=payment_status_data.get("merchant_order_id")
                ).first()

                if existing_txn:
                    return Response({
                        "message": "Duplicate callback ignored",
                        "transaction_id": existing_txn.transaction_id
                    }, status=200)

                # Step 2: Amount calculation
                new_status = "booked"
                paid_amount = property_obj.booking_amount
                remaining_amount = property_obj.property_value_without_booking_amount
                date_field = "booking_date"

                # Step 3: Prevent duplicate bookings
                if UserProperty.objects.filter(user=user, property=property_obj, status=new_status).exists():
                    return Response({"error": "Property already booked by this user"}, status=400)

                if property_obj.status == "purchased":
                    return Response({"error": "Property already purchased"}, status=400)

                # Step 4: Generate document number
                doc_number = generate_transaction_doc_number()
                if doc_file:
                    ext = os.path.splitext(doc_file.name)[1]
                    doc_file.name = f"{doc_number}{ext}"

                # ---------------------------------------------------------
                # Step 5: CREATE TRANSACTION (Only ONE allowed)
                # ---------------------------------------------------------
                transaction = Transaction.objects.create(
                    user_id=user,
                    property_id=property_obj,
                    property_name=property_obj.property_title,
                    property_value=property_obj.total_property_value,
                    remaining_amount=remaining_amount,
                    company_commission=property_obj.company_commission,
                    transaction_for="property",
                    role=role_str,
                    paid_amount=paid_amount,
                    payment_mode=payment_mode,
                    phone_pe_merchant_order_id=payment_status_data.get("merchant_order_id"),
                    phone_pe_order_id=payment_status_data.get("order_id"),
                    phone_pe_transaction_id=phone_pe_transaction_id,
                    payment_type=payment_type,
                    document_number=doc_number,
                    document_file=doc_file,
                )

                # Step 6: Generate invoice PDF
                generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type)

                # Step 7: Update UserProperty & Property
                user_property, created = UserProperty.objects.get_or_create(
                    user=user,
                    property=property_obj,
                    defaults={"status": new_status, date_field: timezone.now().date()}
                )

                if not created:
                    user_property.status = new_status
                    setattr(user_property, date_field, timezone.now().date())
                    user_property.save()

                if property_obj.status == "available":
                    property_obj.status = "booked"
                    property_obj.save()

                return Response({"message": "Booking payment confirmed"}, status=201)

            # ---------------------------------------------------------
            # CASE 2: Full Amount (Manual Cash Payment)
            # ---------------------------------------------------------
            elif payment_type == "Full-Amount":

                paid_amount = float(property_obj.property_value_without_booking_amount)

                # Step 1: Generate document number
                doc_number = generate_transaction_doc_number()
                if cash_receipt:
                    ext = os.path.splitext(cash_receipt.name)[1]
                    cash_receipt.name = f"{doc_number}{ext}"

                # Step 2: Prevent duplicates
                if UserProperty.objects.filter(user=user, property=property_obj, status="purchased").exists():
                    return Response({"error": "Already Purchased"}, status=400)

                if property_obj.status == "purchased":
                    return Response({"error": "Property already purchased"}, status=400)

                # Step 3: Create transaction
                transaction = Transaction.objects.create(
                    user_id=user,
                    username=user.username,
                    property_id=property_obj,
                    property_name=property_obj.property_title,
                    property_value=property_obj.total_property_value,
                    remaining_amount=0,
                    company_commission=property_obj.company_commission,
                    transaction_for="property",
                    role=role_str,
                    paid_amount=paid_amount,
                    payment_mode="Cash",
                    payment_type="Full-Amount",
                    document_number=doc_number,
                    document_file=cash_receipt,
                )

                # Step 4: Generate invoice
                generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type)

                # Step 5: Update user-property
                user_property, _ = UserProperty.objects.get_or_create(
                    user=user,
                    property=property_obj,
                    defaults={"status": "purchased", "purchase_date": timezone.now().date()}
                )
                user_property.status = "purchased"
                user_property.purchase_date = timezone.now().date()
                user_property.save()

                # Step 6: Update property status
                property_obj.status = "purchased"
                property_obj.save()

                return Response({"message": "Full payment processed"}, status=201)

            else:
                return Response({"error": "Invalid payment_type"}, status=400)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Property.DoesNotExist:
            return Response({"error": "Property not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)






class ProductInitiatePaymentAPIView_old(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            redirect_url = request.data.get("redirect_url")
            payment_method = request.data.get("payment_method")  # "online" or "cod"

            if not user_id or not payment_method:
                return Response({"error": "user_id and payment_method required"}, status=400)

            user = User.objects.get(user_id=user_id)
            cart_items = Cart.objects.filter(user=user)

            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=400)

            total_amount = 0

            # STEP 1: Stock validation (variants only)
            for item in cart_items:
                if item.variant and item.variant.stock < item.quantity:
                    return Response(
                        {"error": f"Insufficient stock for {item.variant.sku}"},
                        status=400
                    )

            # STEP 2: Create Order
            order = Order.objects.create(user=user, status="pending")

            # STEP 3: Create OrderItems
            for item in cart_items:
                if item.variant:
                    price = item.variant.selling_price or item.variant.mrp
                    OrderItem.objects.create(
                        order=order,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=price
                    )
                    total_amount += price * item.quantity

                elif item.property_item:
                    price = item.property_item.total_property_value
                    OrderItem.objects.create(
                        order=order,
                        property_item=item.property_item,
                        quantity=1,
                        price=price
                    )
                    total_amount += price

            order.total_amount = total_amount
            order.save(update_fields=["total_amount"])

            # =========================
            # ✅ CASE 1: CASH ON DELIVERY
            # =========================
            if payment_method == "cod":
                Transaction.objects.create(
                    user_id=user,
                    transaction_for="product",
                    order=order,
                    paid_amount=0,
                    payment_method="COD",
                    status="pending"
                )

                # ✅ CLEAR CART IMMEDIATELY FOR COD
                Cart.objects.filter(user=user).delete()

                return Response({
                    "message": "Order placed with Cash on Delivery",
                    "order_id": order.order_id,
                    "amount": total_amount,
                    "payment_method": "cod"
                }, status=200)

            # =========================
            # ✅ CASE 2: ONLINE PAYMENT
            # =========================
            if payment_method == "online":
                if not redirect_url:
                    return Response({"error": "redirect_url required for online payment"}, status=400)

                amount_in_paise = int(total_amount * 100)
                result = initiate_payment(amount=amount_in_paise, redirect_url=redirect_url)

                Transaction.objects.create(
                    user_id=user,
                    transaction_for="product",
                    order=order,
                    paid_amount=total_amount,
                    status="pending",
                    payment_method="ONLINE",
                    phone_pe_merchant_order_id=result["merchant_order_id"]
                )

                return Response({
                    "order_id": order.order_id,
                    "merchant_order_id": result["merchant_order_id"],
                    "payment_url": result["redirect_url"],
                    "amount": total_amount,
                    "payment_method": "online"
                }, status=200)

            return Response({"error": "Invalid payment_method"}, status=400)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)







class ProductInitiatePaymentAPIView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            redirect_url = request.data.get("redirect_url")
            payment_method = request.data.get("payment_method")  # "online" or "cod"

            shipping_address = request.data.get("shipping_address")
            billing_address = request.data.get("billing_address")

            if not user_id or not payment_method:
                return Response({"error": "user_id and payment_method required"}, status=400)

            if not shipping_address:
                return Response({"error": "shipping_address is required"}, status=400)

            user = User.objects.get(user_id=user_id)
            cart_items = Cart.objects.filter(user=user)

            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=400)

            total_amount = 0

            # STEP 1: Stock validation (variants only)
            for item in cart_items:
                if item.variant and item.variant.stock < item.quantity:
                    return Response(
                        {"error": f"Insufficient stock for {item.variant.sku}"},
                        status=400
                    )

            with db_transaction.atomic():
                # STEP 2: Create Order
                order = Order.objects.create(user=user, status="pending")

                # STEP 3: Create OrderItems
                for item in cart_items:
                    if item.variant:
                        price = item.variant.selling_price or item.variant.mrp
                        OrderItem.objects.create(
                            order=order,
                            variant=item.variant,
                            quantity=item.quantity,
                            price=price
                        )
                        total_amount += price * item.quantity

                    elif item.property_item:
                        price = item.property_item.total_property_value
                        OrderItem.objects.create(
                            order=order,
                            property_item=item.property_item,
                            quantity=1,
                            price=price
                        )
                        total_amount += price

                order.total_amount = total_amount
                order.save(update_fields=["total_amount"])

                # STEP 4: Save Shipping Address
                OrderAddress.objects.create(
                    order=order,
                    address_type="shipping",
                    full_name=shipping_address.get("full_name"),
                    phone=shipping_address.get("phone"),
                    address_line1=shipping_address.get("address_line1"),
                    address_line2=shipping_address.get("address_line2"),
                    city=shipping_address.get("city"),
                    state=shipping_address.get("state"),
                    pincode=shipping_address.get("pincode"),
                    country=shipping_address.get("country", "India"),
                )

                # STEP 5: Save Billing Address (optional)
                if billing_address:
                    OrderAddress.objects.create(
                        order=order,
                        address_type="billing",
                        full_name=billing_address.get("full_name"),
                        phone=billing_address.get("phone"),
                        address_line1=billing_address.get("address_line1"),
                        address_line2=billing_address.get("address_line2"),
                        city=billing_address.get("city"),
                        state=billing_address.get("state"),
                        pincode=billing_address.get("pincode"),
                        country=billing_address.get("country", "India"),
                    )

                # =========================
                # ✅ CASE 1: CASH ON DELIVERY
                # =========================
                if payment_method == "cod":
                    Transaction.objects.create(
                        user_id=user,
                        transaction_for="product",
                        order=order,
                        paid_amount=0,
                        payment_method="COD",
                        status="pending"
                    )

                    # ✅ CLEAR CART IMMEDIATELY FOR COD
                    Cart.objects.filter(user=user).delete()

                    return Response({
                        "message": "Order placed with Cash on Delivery",
                        "order_id": order.order_id,
                        "amount": total_amount,
                        "payment_method": "cod"
                    }, status=200)

                # =========================
                # ✅ CASE 2: ONLINE PAYMENT
                # =========================
                if payment_method == "online":
                    if not redirect_url:
                        return Response({"error": "redirect_url required for online payment"}, status=400)

                    amount_in_paise = int(total_amount * 100)
                    result = initiate_payment(amount=amount_in_paise, redirect_url=redirect_url)

                    Transaction.objects.create(
                        user_id=user,
                        transaction_for="product",
                        order=order,
                        paid_amount=total_amount,
                        status="pending",
                        payment_method="ONLINE",
                        phone_pe_merchant_order_id=result["merchant_order_id"]
                    )

                    return Response({
                        "order_id": order.order_id,
                        "merchant_order_id": result["merchant_order_id"],
                        "payment_url": result["redirect_url"],
                        "amount": total_amount,
                        "payment_method": "online"
                    }, status=200)

                return Response({"error": "Invalid payment_method"}, status=400)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

def format_variant_attributes(attrs):
    if not attrs:
        return "-"

    # if stored as dict: {"Color": "Red", "Size": "XL"}
    if isinstance(attrs, dict):
        return " / ".join(f"{k}: {v}" for k, v in attrs.items())

    # if stored as list: [{"Color": "Red"}, {"Size": "XL"}]
    if isinstance(attrs, list):
        kv_pairs = []
        for d in attrs:
            if isinstance(d, dict):
                kv_pairs.extend(f"{k}: {v}" for k, v in d.items())
        if kv_pairs:
            return " / ".join(kv_pairs)

    # fallback for unexpected formats
    return str(attrs)







class ProductConfirmPaymentAPIView(APIView):

    def notify_user(self, users, message, product=None, product_variant=None, property_obj=None):
        notification = Notification.objects.create(
            message=message,
            product=product,
            product_variant=product_variant,
            property=property_obj
        )
        notification.visible_to_users.set(users)

        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(user=u, notification=notification, is_read=False)
            for u in users
        ])

    def post(self, request):
        try:
            merchant_order_id = request.data.get("merchant_order_id")

            if not merchant_order_id:
                return Response({"error": "merchant_order_id required"}, status=400)

            payment_status_data = check_payment_status(merchant_order_id)

            if payment_status_data.get("status") != "COMPLETED":
                return Response(
                    {**payment_status_data, "message": "Payment not completed"},
                    status=202
                )

            with db_transaction.atomic():

                txn = Transaction.objects.select_for_update().get(
                    phone_pe_merchant_order_id=merchant_order_id,
                    status="pending"
                )

                order = txn.order
                user = txn.user_id

                # Deduct stock for variants only
                for item in order.items.select_related("variant"):
                    if item.variant:
                        if item.variant.stock < item.quantity:
                            raise Exception("Stock mismatch")
                        item.variant.stock -= item.quantity
                        item.variant.save(update_fields=["stock"])

                # Extract phonepe payment details
                payment_details = payment_status_data.get("payment_details", [])

                txn.phone_pe_transaction_id = (
                    payment_details[0]["transaction_id"] if payment_details else None
                )
                txn.payment_mode = (
                    payment_details[0]["payment_mode"] if payment_details else None
                )
                txn.phone_pe_order_id = payment_status_data.get("order_id")

                txn.status = "success"
                txn.document_number = generate_transaction_doc_number()
                txn.save(update_fields=[
                    "status",
                    "document_number",
                    "phone_pe_transaction_id",
                    "phone_pe_order_id",
                    "payment_mode"
                ])

                order.status = "paid"
                order.save(update_fields=["status"])

                Cart.objects.filter(user=user).delete()

            # Generate Invoice PDF
            generate_product_invoice_pdf(transaction=txn, order=order, user=user)

            # ================= EMAIL SECTION =================

            buyer_email = user.email
            buyer_phone = getattr(user, "phone_number", "")
            buyer_first = getattr(user, "first_name", "")
            buyer_last = getattr(user, "last_name", "")

            # Group seller emails
            seller_map = {}  # key: email, value: list of order items

            for item in order.items.all():

                if item.variant:
                    business = item.variant.product.business
                    email = business.support_email
                    seller_map.setdefault(email, []).append(item)

                elif item.property_item:
                    owner = item.property_item.owner
                    if owner and owner.email:
                        email = owner.email
                        seller_map.setdefault(email, []).append(item)

            # SEND SELLER EMAILS
            for seller_email, items in seller_map.items():
                lines = []
                lines.append(f"A new order #{order.order_id} has been placed.\n")
                lines.append("Buyer Details:")
                lines.append(f"First Name: {buyer_first}")
                lines.append(f"Last Name: {buyer_last}")
                lines.append(f"Phone: {buyer_phone}")
                lines.append(f"Email: {buyer_email}\n")
                lines.append("Order Items:")

                for item in items:
                    if item.variant:
                        product = item.variant.product
                        attrs = format_variant_attributes(item.variant.attributes)
                        lines.append(
                            f"Product: {product.product_name} ({attrs}) | Qty: {item.quantity} | Price: {item.price}"
                        )
                    else:
                        p = item.property_item
                        lines.append(
                            f"Property: {p.property_title} | Qty: {item.quantity} | Price: {item.price}"
                        )

                lines.append(f"\nOrder Total: {order.total_amount}")

                send_mail(
                    subject=f"New Order #{order.order_id}",
                    message="\n".join(lines),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[seller_email],
                    fail_silently=True
                )

            # SEND BUYER EMAIL
            buyer_lines = []
            buyer_lines.append(f"Your order #{order.order_id} has been successfully placed!\n")

            buyer_lines.append("Buyer Details:")
            buyer_lines.append(f"First Name: {buyer_first}")
            buyer_lines.append(f"Last Name: {buyer_last}")
            buyer_lines.append(f"Phone: {buyer_phone}")
            buyer_lines.append(f"Email: {buyer_email}\n")

            buyer_lines.append("Order Items:")

            for item in order.items.all():
                if item.variant:
                    product = item.variant.product
                    business = product.business
                    attrs = format_variant_attributes(item.variant.attributes)
                    buyer_lines.append(
                        f"Product: {product.product_name} ({attrs}) | Business: {business.business_name} | Qty: {item.quantity} | Price: {item.price}"
                    )
                else:
                    p = item.property_item
                    owner = p.owner
                    buyer_lines.append(
                        f"Property: {p.property_title} | Owner: {owner.first_name} {owner.last_name} | Qty: {item.quantity} | Price: {item.price}"
                    )

            buyer_lines.append(f"\nOrder Total: {order.total_amount}")

            send_mail(
                subject=f"Order Confirmation #{order.order_id}",
                message="\n".join(buyer_lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[buyer_email],
                fail_silently=True
            )

            # ================= IN-APP NOTIFICATIONS =================

            admin_users = list(User.objects.filter(roles__role_name="Admin").distinct())

            # Create item-specific notifications so product & variant are never NULL
            for item in order.items.select_related("variant", "property_item", "variant__product"):

                # ---------- PRODUCT ITEM ----------
                if item.variant:
                    product = item.variant.product
                    variant = item.variant
                    seller = product.business.user

                    # Buyer
                    self.notify_user(
                        users=[user],
                        message=f"Your order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been successfully placed.",
                        product=product,
                        product_variant=variant
                    )

                    # Seller
                    self.notify_user(
                        users=[seller],
                        message=f"You received a new order #{order.order_id} for {product.product_name} (SKU: {variant.sku}).",
                        product=product,
                        product_variant=variant
                    )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"New order #{order.order_id} placed for {product.product_name} (SKU: {variant.sku}).",
                            product=product,
                            product_variant=variant
                        )

                # ---------- PROPERTY ITEM ----------
                elif item.property_item:
                    prop = item.property_item
                    owner = prop.owner

                    # Buyer
                    self.notify_user(
                        users=[user],
                        message=f"Your order #{order.order_id} for property '{prop.property_title}' has been successfully placed.",
                        property_obj=prop
                    )

                    # Owner
                    if owner:
                        self.notify_user(
                            users=[owner],
                            message=f"You received a new order #{order.order_id} for your property '{prop.property_title}'.",
                            property_obj=prop
                        )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"New order #{order.order_id} placed for property '{prop.property_title}'.",
                            property_obj=prop
                        )

            return Response({"message": "Payment successful", **payment_status_data}, status=201)

        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)







class ConfirmCODPaymentAPIView(APIView):

    def notify_user(self, users, message, product=None, product_variant=None, property_obj=None):
        notification = Notification.objects.create(
            message=message,
            product=product,
            product_variant=product_variant,
            property=property_obj
        )
        notification.visible_to_users.set(users)

        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(user=u, notification=notification, is_read=False)
            for u in users
        ])

    def post(self, request, order_id):
        try:
            with db_transaction.atomic():
                order = Order.objects.select_for_update().get(order_id=order_id)

                txn = Transaction.objects.select_for_update().get(
                    order=order,
                    payment_method="COD",
                    status="pending"
                )

                user = order.user

                # Mark transaction as successful (cash collected)
                txn.status = "success"
                txn.paid_amount = order.total_amount
                txn.document_number = generate_transaction_doc_number()
                txn.save(update_fields=["status", "paid_amount", "document_number"])

                # Mark order as delivered
                order.status = "delivered"
                order.save(update_fields=["status"])

            # ================= GENERATE INVOICE =================
            generate_product_invoice_pdf(transaction=txn, order=order, user=user)

            # ================= EMAIL SECTION =================

            buyer_email = user.email
            buyer_phone = getattr(user, "phone_number", "")
            buyer_first = getattr(user, "first_name", "")
            buyer_last = getattr(user, "last_name", "")

            # Group seller emails
            seller_map = {}  # key: email, value: list of order items

            for item in order.items.all():
                if item.variant:
                    business = item.variant.product.business
                    email = business.support_email
                    seller_map.setdefault(email, []).append(item)

                elif item.property_item:
                    owner = item.property_item.owner
                    if owner and owner.email:
                        email = owner.email
                        seller_map.setdefault(email, []).append(item)

            # SEND SELLER EMAILS
            for seller_email, items in seller_map.items():
                lines = []
                lines.append(f"COD Order #{order.order_id} has been delivered and payment received.\n")
                lines.append("Buyer Details:")
                lines.append(f"First Name: {buyer_first}")
                lines.append(f"Last Name: {buyer_last}")
                lines.append(f"Phone: {buyer_phone}")
                lines.append(f"Email: {buyer_email}\n")
                lines.append("Order Items:")

                for item in items:
                    if item.variant:
                        product = item.variant.product
                        attrs = format_variant_attributes(item.variant.attributes)
                        lines.append(
                            f"Product: {product.product_name} ({attrs}) | Qty: {item.quantity} | Price: {item.price}"
                        )
                    else:
                        p = item.property_item
                        lines.append(
                            f"Property: {p.property_title} | Qty: {item.quantity} | Price: {item.price}"
                        )

                lines.append(f"\nOrder Total: {order.total_amount}")

                send_mail(
                    subject=f"COD Order Delivered #{order.order_id}",
                    message="\n".join(lines),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[seller_email],
                    fail_silently=True
                )

            # SEND BUYER EMAIL
            buyer_lines = []
            buyer_lines.append(f"Your COD order #{order.order_id} has been delivered successfully and payment received!\n")

            buyer_lines.append("Buyer Details:")
            buyer_lines.append(f"First Name: {buyer_first}")
            buyer_lines.append(f"Last Name: {buyer_last}")
            buyer_lines.append(f"Phone: {buyer_phone}")
            buyer_lines.append(f"Email: {buyer_email}\n")

            buyer_lines.append("Order Items:")

            for item in order.items.all():
                if item.variant:
                    product = item.variant.product
                    business = product.business
                    attrs = format_variant_attributes(item.variant.attributes)
                    buyer_lines.append(
                        f"Product: {product.product_name} ({attrs}) | Business: {business.business_name} | Qty: {item.quantity} | Price: {item.price}"
                    )
                else:
                    p = item.property_item
                    owner = p.owner
                    buyer_lines.append(
                        f"Property: {p.property_title} | Owner: {owner.first_name} {owner.last_name} | Qty: {item.quantity} | Price: {item.price}"
                    )

            buyer_lines.append(f"\nOrder Total: {order.total_amount}")

            send_mail(
                subject=f"COD Order Delivered #{order.order_id}",
                message="\n".join(buyer_lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[buyer_email],
                fail_silently=True
            )

            # ================= IN-APP NOTIFICATIONS =================

            admin_users = list(User.objects.filter(roles__role_name="Admin").distinct())

            for item in order.items.select_related("variant", "property_item", "variant__product"):

                # ---------- PRODUCT ITEM ----------
                if item.variant:
                    product = item.variant.product
                    variant = item.variant
                    seller = product.business.user

                    # Buyer
                    self.notify_user(
                        users=[user],
                        message=f"Your COD order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been delivered and payment received.",
                        product=product,
                        product_variant=variant
                    )

                    # Seller
                    self.notify_user(
                        users=[seller],
                        message=f"COD order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been delivered and marked as paid.",
                        product=product,
                        product_variant=variant
                    )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"COD order #{order.order_id} delivered and payment confirmed for {product.product_name} (SKU: {variant.sku}).",
                            product=product,
                            product_variant=variant
                        )

                # ---------- PROPERTY ITEM ----------
                elif item.property_item:
                    prop = item.property_item
                    owner = prop.owner

                    # Buyer
                    self.notify_user(
                        users=[user],
                        message=f"Your COD order #{order.order_id} for property '{prop.property_title}' has been delivered and payment received.",
                        property_obj=prop
                    )

                    # Owner
                    if owner:
                        self.notify_user(
                            users=[owner],
                            message=f"COD order #{order.order_id} for your property '{prop.property_title}' has been delivered and marked as paid.",
                            property_obj=prop
                        )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"COD order #{order.order_id} delivered and payment confirmed for property '{prop.property_title}'.",
                            property_obj=prop
                        )

            return Response({"message": "COD order delivered and payment confirmed"}, status=200)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Transaction.DoesNotExist:
            return Response({"error": "Pending COD transaction not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)






class CancelOrderAPIView(APIView):

    def notify_user(self, users, message, product=None, product_variant=None, property_obj=None):
        notification = Notification.objects.create(
            message=message,
            product=product,
            product_variant=product_variant,
            property=property_obj
        )
        notification.visible_to_users.set(users)

        UserNotificationStatus.objects.bulk_create([
            UserNotificationStatus(user=u, notification=notification, is_read=False)
            for u in users
        ])

    def post(self, request, order_id):
        try:
            with db_transaction.atomic():
                order = Order.objects.select_for_update().get(order_id=order_id)

                # ❌ Do not allow cancel after delivery
                if order.status == "delivered":
                    return Response(
                        {"error": "Delivered orders cannot be cancelled"},
                        status=400
                    )

                # Already cancelled?
                if order.status == "cancelled":
                    return Response(
                        {"message": "Order already cancelled"},
                        status=200
                    )

                # Lock related transaction (if any)
                txn = Transaction.objects.select_for_update().filter(order=order).first()

                # Restore stock for variants
                for item in order.items.select_related("variant"):
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save(update_fields=["stock"])

                # Update order status
                order.status = "cancelled"
                order.save(update_fields=["status"])

                refund_done = False

                # Handle payment side
                if txn:
                    # ONLINE PAYMENT: if already paid, mark refunded
                    if txn.payment_mode == "ONLINE" and txn.status == "success":
                        # TODO: Call actual payment gateway refund API here if available
                        txn.status = "refunded"
                        txn.save(update_fields=["status"])
                        refund_done = True

                    # COD: just mark transaction as failed/cancelled-like
                    elif txn.payment_mode == "COD" and txn.status == "pending":
                        txn.status = "failed"
                        txn.save(update_fields=["status"])

                user = order.user

            # ================= IN-APP NOTIFICATIONS =================

            admin_users = list(User.objects.filter(roles__role_name="Admin").distinct())

            for item in order.items.select_related("variant", "property_item", "variant__product"):

                # ---------- PRODUCT ITEM ----------
                if item.variant:
                    product = item.variant.product
                    variant = item.variant
                    seller = product.business.user

                    # Buyer
                    buyer_msg = (
                        f"Your order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been cancelled."
                    )
                    if refund_done:
                        buyer_msg += " Refund has been initiated."

                    self.notify_user(
                        users=[user],
                        message=buyer_msg,
                        product=product,
                        product_variant=variant
                    )

                    # Seller
                    self.notify_user(
                        users=[seller],
                        message=f"Order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been cancelled by the buyer.",
                        product=product,
                        product_variant=variant
                    )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"Order #{order.order_id} for {product.product_name} (SKU: {variant.sku}) has been cancelled.",
                            product=product,
                            product_variant=variant
                        )

                # ---------- PROPERTY ITEM ----------
                elif item.property_item:
                    prop = item.property_item
                    owner = prop.owner

                    # Buyer
                    buyer_msg = (
                        f"Your order #{order.order_id} for property '{prop.property_title}' has been cancelled."
                    )
                    if refund_done:
                        buyer_msg += " Refund has been initiated."

                    self.notify_user(
                        users=[user],
                        message=buyer_msg,
                        property_obj=prop
                    )

                    # Owner
                    if owner:
                        self.notify_user(
                            users=[owner],
                            message=f"Order #{order.order_id} for your property '{prop.property_title}' has been cancelled by the buyer.",
                            property_obj=prop
                        )

                    # Admin
                    if admin_users:
                        self.notify_user(
                            users=admin_users,
                            message=f"Order #{order.order_id} for property '{prop.property_title}' has been cancelled.",
                            property_obj=prop
                        )

            return Response(
                {
                    "message": "Order cancelled successfully",
                    "refund_initiated": refund_done
                },
                status=200
            )

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)