from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


# PHONEPE
from uuid import uuid4
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.env import Env


def get_phonepe_client():
    env_map = {
        "SANDBOX": Env.SANDBOX,
        "PRODUCTION": Env.PRODUCTION
    }

    return StandardCheckoutClient.get_instance(
        client_id=settings.PHONEPE_CLIENT_ID,
        client_secret=settings.PHONEPE_CLIENT_SECRET,
        client_version=settings.PHONEPE_CLIENT_VERSION,
        env=env_map.get(settings.PHONEPE_ENVIRONMENT, Env.SANDBOX),
        should_publish_events=False
    )

class InitiatePaymentAPIView(APIView):
    def post(self, request):
        try:
            client = get_phonepe_client()
            unique_order_id = str(uuid4())

            amount_rupees = request.data.get("amount")
            redirect_url = request.data.get("redirect_url")

            if not amount_rupees or not redirect_url:
                return Response({"error": "amount and redirect_url are required"}, status=400)

            # Convert rupees to paisa
            amount_paisa = int(float(amount_rupees) * 100)

            meta_info = MetaInfo(udf1="udf1", udf2="udf2", udf3="udf3")

            pay_request = StandardCheckoutPayRequest.build_request(
                merchant_order_id=unique_order_id,
                amount=amount_paisa,
                redirect_url=redirect_url,
                meta_info=meta_info
            )

            response = client.pay(pay_request)
            return Response({
                "order_id": unique_order_id,
                "merchant_order_id": unique_order_id,
                "redirect_url": response.redirect_url,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusAPIView(APIView):
    def get(self, request):
        try:
            merchant_order_id = request.GET.get("merchant_order_id")
            if not merchant_order_id:
                return Response({"error": "merchant_order_id is required"}, status=400)

            client = get_phonepe_client()
            response = client.get_order_status(merchant_order_id, details=False)

            payment_details = [
                {
                    "payment_mode": getattr(detail, "payment_mode", None),
                    "amount": getattr(detail, "amount", None),
                    "transaction_id": getattr(detail, "transaction_id", None),
                    "state": getattr(detail, "state", None),
                    "error_code": getattr(detail, "error_code", None),
                    "detailed_error_code": getattr(detail, "detailed_error_code", None),
                    "instrument_type": getattr(detail, "instrumentType", None),  # <-- ✅ Corrected here
                }
                for detail in response.payment_details or []
            ]

            return Response({
                "merchantOrderId": merchant_order_id,
                "status": response.state,
                "amount": response.amount,
                "order_id": response.order_id,
                "payment_details": payment_details,
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
