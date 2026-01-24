from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from decimal import Decimal
from property.models import  *
#from transactions.models import *
from users.models import User
from django.db.models import Sum
from mlm.pagination import GlobalPagination
from django.utils.timezone import now

#from .models import Transaction, CommissionMaster, Commission, Property, User  # Adjust imports if needed


# ------------------ Commission Master Views ------------------

class CommissionMasterListCreateView(APIView):

    def get(self, request):
        try:
            commissions = CommissionMaster.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_commissions = paginator.paginate_queryset(
                commissions,
                request
            )

            serializer = CommissionMasterSerializer(
                paginated_commissions,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = CommissionMasterSerializer(data=request.data)
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
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommissionMasterDetailView(APIView):
    def get(self, request, id):
        try:
            commission = get_object_or_404(CommissionMaster, id=id)
            serializer = CommissionMasterSerializer(commission)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            commission_master = get_object_or_404(CommissionMaster, id=id)
            serializer = CommissionMasterSerializer(commission_master, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            commission_master = get_object_or_404(CommissionMaster, id=id)
            commission_master.delete()
            return Response({"message": "Commission Master deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


