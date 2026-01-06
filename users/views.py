from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from property.models import  *
import random
from django.core.mail import send_mail
from django.utils.cache import caches
from mlm.settings import *
from PIL import Image
from django.db.models import Count, Q, Sum
import random
import requests
from urllib.parse import quote  # ✅ for URL encoding
from django.core.cache import cache
from django.conf import settings
from mlm.pagination import GlobalPagination




# Use Django's cache framework to store OTP temporarily
cache = caches['default']


class LoginAPIView_old(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
            print(user)
            if check_password(password, user.password):
                # Fetch the user's roles
                roles = user.roles.values_list('role_name', flat=True)  # Get role names as a list
                
                return Response(
                    {
                        "message": "Login successful",
                        "user_id": user.user_id,
                        "referral_id":user.referral_id,
                        "referred_by": user.referred_by,
                        "first_name":user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "roles": list(roles),  # Convert QuerySet to list
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)






class LoginAPIView(APIView):
    def post(self, request):
        email_or_phone = request.data.get("email_or_phonenumber")
        password = request.data.get("password")

        if not email_or_phone or not password:
            return Response(
                {"error": "Email/Phone and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Determine whether input is email or phone
            if "@" in email_or_phone:
                user = User.objects.get(email=email_or_phone)   # Login using email
            else:
                user = User.objects.get(phone_number=email_or_phone)  # Login using phone

            # Validate password
            if check_password(password, user.password):

                roles = user.roles.values_list('role_name', flat=True)

                return Response(
                    {
                        "message": "Login successful",
                        "user_id": user.user_id,
                        "referral_id": user.referral_id,
                        "referred_by": user.referred_by,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "roles": list(roles),
                    },
                    status=status.HTTP_200_OK
                )

            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class LoginAPIView1(APIView):
    """
    Step 1: Send 6-digit OTP via SMS using only phone_number.
    """

    def post(self, request):
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Generate 6-digit OTP
        otp = random.randint(100000, 999999)
        cache.set(f'otp_{phone_number}', otp, timeout=300)  # store OTP for 5 minutes
        cache.set('current_login_phone', phone_number, timeout=300)  # store current phone temporarily

        # ✅ Prepare message
        message = (
            f"Dear Customer {user.first_name}, please use the OTP {otp} "
            f"to log in to the Dashboard - SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED."
        )
        encoded_message = quote(message)

        # ✅ Build SMS URL properly
        sms_url = (
            f"https://www.smsjust.com/blank/sms/user/urlsms.php?"
            f"username=shrirajproperty&pass=user@123&senderid=SHRJTM&"
            f"dest_mobileno={phone_number}&message={encoded_message}&"
            "dltentityid=1101665170000089172&dlttempid=1107175998225544393&response=Y"
        )

        try:
            response = requests.get(sms_url)
            print(sms_url, 'sms_url')
            if response.status_code != 200 or "error" in response.text.lower():
                return Response({"error": f"SMS API error: {response.text}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "message": f"OTP sent successfully to your registered mobile number ending with {phone_number[-4:]}"
            },
            status=status.HTTP_200_OK
        )


class VerifyOTPView(APIView):
    """
    Step 2: Verify OTP only (no phone_number needed).
    """

    def post(self, request):
        otp = request.data.get("otp")

        if not otp:
            return Response({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Retrieve phone number from cache (stored during login step)
        phone_number = cache.get('current_login_phone')

        if not phone_number:
            return Response({"error": "No login session found or OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(f'otp_{phone_number}')

        if stored_otp and str(stored_otp) == str(otp):
            cache.delete(f'otp_{phone_number}')  # remove OTP after verification
            cache.delete('current_login_phone')  # clear temporary login state

            try:
                user = User.objects.get(phone_number=phone_number)
                roles = user.roles.values_list('role_name', flat=True)

                return Response(
                    {
                        "message": "Login successful",
                        "user_id": user.user_id,
                        "referral_id": user.referral_id,
                        "referred_by": user.referred_by,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "roles": list(roles),
                    },
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)



# Logout API 
class LogoutAPIView(APIView):
    def post(self, request):
        return Response({"message": "Logged out successfully!"}, status=status.HTTP_200_OK)
    





class RoleListCreateView(APIView):

    def get(self, request):
        try:
            roles = Role.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_roles = paginator.paginate_queryset(roles, request)

            serializer = RoleSerializer(
                paginated_roles,
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
            serializer = RoleSerializer(data=request.data)
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


class RoleDetailView(APIView):
    def get(self, request, role_id):
        try:
            role = get_object_or_404(Role, role_id=role_id)
            serializer = RoleSerializer(role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, role_id):
        try:
            role = get_object_or_404(Role, role_id=role_id)
            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, role_id):
        try:
            role = get_object_or_404(Role, role_id=role_id)
            role.delete()
            return Response({"message": "Role deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








from django.db import transaction, IntegrityError
from django.db.models import Max, IntegerField
from django.db.models.functions import Cast, Substr





class UserListCreateView(APIView):

    def get(self, request):
        try:
            users = User.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_users = paginator.paginate_queryset(users, request)

            serializer = UserSerializer(
                paginated_users,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic()
    def post(self, request):
        try:
            data = request.data.copy()

            # ---------------- Validate referred_by ----------------
            referred_by = data.get("referred_by")
            if referred_by:
                if not User.objects.filter(referral_id=referred_by).exists():
                    return Response(
                        {"error": "Invalid referral code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # ---------------- Detect Agent role ----------------
            role_ids = data.getlist("role_ids") if hasattr(data, "getlist") else data.get("role_ids", [])
            if isinstance(role_ids, str):
                role_ids = [role_ids]

            is_agent = Role.objects.filter(
                role_id__in=role_ids,
                role_name="Agent"
            ).exists()

            referral_id = None

            if is_agent:
                #prefix_obj = ReferralPrefix.objects.last()
                # prefix = prefix_obj.prefix if prefix_obj else "SRT"
                prefix = "SRP"

                # 🔐 LOCK all users having referral_id
                latest_referral = (
                    User.objects
                        .select_for_update()
                        .exclude(referral_id__isnull=True)
                        .exclude(referral_id="")
                        .annotate(
                            num=Cast(
                                Substr("referral_id", 4),  # remove prefix (first 3 chars)
                                IntegerField()
                            )
                        )
                        .aggregate(max_num=Max("num"))
                )

                next_number = (latest_referral["max_num"] or 0) + 1
                referral_id = f"{prefix}{str(next_number).zfill(6)}"

            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            try:
                user = serializer.save(referral_id=referral_id)
            except IntegrityError:
                return Response(
                    {"error": "Duplicate referral detected, please retry"},
                    status=status.HTTP_409_CONFLICT
                )

            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = get_object_or_404(User, user_id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, user_id):
        try:
            user = get_object_or_404(User, user_id=user_id)
            data = request.data.copy()
            # if 'password' in data:
            #     data['password'] = make_password(data['password'])  # Hash new password need to remove
            serializer = UserSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id):
        try:
            user = get_object_or_404(User, user_id=user_id)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    


class UsersByRoleAPIView(APIView):
    def get(self, request, role_name):
        try:
            role = Role.objects.get(role_name=role_name)
            users = User.objects.filter(roles=role).distinct()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=200)
        except Role.DoesNotExist:
            return Response({"error": f"Role '{role_name}' not found"}, status=404)



class UsersByStatus(APIView):
    def get(self, request, user_status):
        try:
            users = User.objects.filter(status=user_status)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class AgentsByReferralIdAPIView(APIView):
    def get(self, request, referral_id):
        try:
            users = User.objects.filter(referred_by=referral_id).order_by('created_at')
            active_users = users.filter(status__iexact='Active')
            inactive_users = users.filter(status__iexact='Inactive')

            users_serializer = UserSerializer(users, many=True)
            active_serializer = UserSerializer(active_users, many=True)
            inactive_serializer = UserSerializer(inactive_users, many=True)

            return Response({
                "total_agents": users.count(),
                "total_active_agents": active_users.count(),
                "total_inactive_agents": inactive_users.count(),
                "agents": users_serializer.data,
                "active_agents": active_serializer.data,
                "inactive_agents": inactive_serializer.data
            }, status=200)
        except User.DoesNotExist:
            return Response({"error": f"Users with referral ID '{referral_id}' not found"}, status=404)




class CountAPIView(APIView):
    def get(self, request):
        one_month_ago = timezone.now() - timedelta(days=30)

        # User role & status counts
        user_counts = User.objects.aggregate(
            total_admins=Count('user_id', filter=Q(roles__role_name__iexact='Admin'), distinct=True),
            total_clients=Count('user_id', filter=Q(roles__role_name__iexact='Client'), distinct=True),
            total_agents=Count('user_id', filter=Q(roles__role_name__iexact='Agent'), distinct=True),
            total_active_users=Count('user_id', filter=Q(status__iexact="Active"), distinct=True),
            total_inactive_users=Count('user_id', filter=Q(status__iexact="Inactive"), distinct=True),
        )

        # Property status & approval counts
        property_counts = Property.objects.aggregate(
            total_properties=Count('property_id', distinct=True),
            total_latest_properties=Count('property_id', filter=Q(created_at__gte=one_month_ago), distinct=True),

            # Property status
            total_sold_properties=Count('property_id', filter=Q(status__iexact='Sold'), distinct=True),
            total_booked_properties=Count('property_id', filter=Q(status__iexact='Booked'), distinct=True),
            total_available_properties=Count('property_id', filter=Q(status__iexact='Available'), distinct=True),

            # Property approval
            total_pending_properties=Count('property_id', filter=Q(approval_status__iexact='Pending'), distinct=True),
            total_approved_properties=Count('property_id', filter=Q(approval_status__iexact='Approved'), distinct=True),
            total_rejected_properties=Count('property_id', filter=Q(approval_status__iexact='Rejected'), distinct=True),
        )

        # Commission totals
        commission_totals = Property.objects.aggregate(
            total_agent_commission=Sum('agent_commission'),
            total_agent_commission_paid=Sum('agent_commission_paid'),
            total_agent_commission_balance=Sum('agent_commission_balance'),

            total_company_commission=Sum('company_commission'),
            total_company_commission_paid=Sum('total_company_commission_distributed'),
            total_remaining_company_commission=Sum('remaining_company_commission'),
        )

        # Replace None with 0.00
        for key in commission_totals:
            commission_totals[key] = commission_totals[key] if commission_totals[key] is not None else 0.00

        # Combine all counts
        counts = {
            **user_counts,
            **property_counts,
            **commission_totals,
        }

        return Response(counts, status=status.HTTP_200_OK)

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        otp = random.randint(1000, 9999)  # Generate a 4-digit OTP
        cache.set(f'otp_{email}', otp, timeout=300)  # Store OTP for 5 minutes
        
        # Send OTP via email
        send_mail(
            subject='Password Reset OTP',
            message=f'Your OTP for password reset is {otp}. It is valid for 5 minutes.',
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)






class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        if not email or not new_password:
            return Response({'error': 'Email and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        otp_verified = cache.get(f'otp_verified_{email}')
        if not otp_verified:
            return Response({'error': 'OTP not verified or session expired'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()
            cache.delete(f'otp_verified_{email}')  # Clean up the flag
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)








class VerifyOTPAndResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(f'otp_{email}')
        if stored_otp and str(stored_otp) == str(otp):
            cache.delete(f'otp_{email}')

            # Case 1: Only verify OTP
            if not new_password:
                cache.set(f'otp_verified_{email}', True, timeout=300)
                return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)

            # Case 2: OTP + new password provided → reset password
            try:
                user = User.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()
                return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)





#Department

class DepartmentListCreateView(APIView):

    def get(self, request):
        try:
            departments = Department.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_departments = paginator.paginate_queryset(
                departments,
                request
            )

            serializer = DepartmentSerializer(
                paginated_departments,
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
            serializer = DepartmentSerializer(data=request.data)
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




class DepartmentDetailView(APIView):
    def get(self, request, id):
        try:
            department = get_object_or_404(Department, id=id)
            serializer = DepartmentSerializer(department)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            department = get_object_or_404(Department, id=id)
            serializer = DepartmentSerializer(department, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            department = get_object_or_404(Department, id=id)
            department.delete()
            return Response({'message': 'Department deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#Meetings
# class MeetingListCreateView(APIView):
#     def get(self, request):
#         try:
#             meetings = Meeting.objects.all().order_by('-scheduled_date')
#             serializer = MeetingSerializer(meetings, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request):
#         try:
#             serializer = MeetingSerializer(data=request.data)
#             if serializer.is_valid():
#                 meeting = serializer.save()

#                 # Extract users for email
#                 recipients = meeting.users.all()


#                 # Format date as DD-MM-YYYY
#                 formatted_date = meeting.scheduled_date.strftime("%d-%m-%Y")

#                 # Send email to all users
#                 subject = f"Meeting Scheduled: {meeting.title}"
#                 message = (
#                     f"Dear Participant,\n\n"
#                     f"You have been added to a new meeting.\n\n"
#                     f"Title: {meeting.title}\n"
#                     f"Date: {formatted_date}\n"
#                     f"Time: {meeting.scheduled_time}\n"
#                     f"Meeting Link: {meeting.meeting_link}\n\n"
#                     f"Notes: {meeting.notes}\n\n"
#                     f"Thank you!"
#                 )

#                 for user in recipients:
#                     if user.email:
#                         send_mail(
#                             subject,
#                             message,
#                             settings.EMAIL_HOST_USER,
#                             [user.email],
#                             fail_silently=False,
#                         )

#                 return Response({"message": "Meeting created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)

#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class MeetingDetailView(APIView):

#     def get(self, request, meeting_id):
#         try:
#             meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
#             serializer = MeetingSerializer(meeting)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     def put(self, request, meeting_id):
#         try:
#             meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
#             old_status = meeting.status

#             serializer = MeetingSerializer(meeting, data=request.data, partial=True)
#             if serializer.is_valid():
#                 updated_meeting = serializer.save()

#                 new_status = updated_meeting.status
#                 # Format date as DD-MM-YYYY
#                 formatted_date = updated_meeting.scheduled_date.strftime("%d-%m-%Y")

#                 # Send email only if status changed
#                 if old_status != new_status and new_status in ["completed", "cancelled"]:
#                     recipients = updated_meeting.users.all()

#                     subject = f"Meeting {new_status.capitalize()}"
#                     message = (
#                         f"Your meeting has been {new_status}.\n\n"
#                         f"Title: {updated_meeting.title}\n"
#                         f"Date: {formatted_date}\n"
#                         f"Time: {updated_meeting.scheduled_time}\n"
#                         f"Link: {updated_meeting.meeting_link or 'N/A'}\n\n"
#                         f"Notes: {updated_meeting.notes}\n"
#                     )

#                     for user in recipients:
#                         if user.email:
#                             send_mail(
#                                 subject,
#                                 message,
#                                 settings.EMAIL_HOST_USER,
#                                 [user.email],
#                                 fail_silently=False,
#                             )

#                 return Response(serializer.data, status=status.HTTP_200_OK)

#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     def delete(self, request, meeting_id):
#         try:
#             meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
#             meeting.delete()
#             return Response({"message": "Meeting deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Meeting Requests

class MeetingRequestListCreateView(APIView):

    def get(self, request):
        try:
            requests = MeetingRequest.objects.all().order_by('-created_at')

            paginator = GlobalPagination()
            paginated_requests = paginator.paginate_queryset(
                requests,
                request
            )

            serializer = MeetingRequestSerializer(
                paginated_requests,
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
            serializer = MeetingRequestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Meeting request created successfully",
                        "data": serializer.data
                    },
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


class MeetingRequestDetailView(APIView):
    def get(self, request, request_id):
        try:
            req = get_object_or_404(MeetingRequest, request_id=request_id)
            serializer = MeetingRequestSerializer(req)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, request_id):
        try:
            req = get_object_or_404(MeetingRequest, request_id=request_id)
            serializer = MeetingRequestSerializer(req, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, request_id):
        try:
            req = get_object_or_404(MeetingRequest, request_id=request_id)
            req.delete()
            return Response({"message": "Meeting request deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class ScheduledMeetingListCreateView(APIView):

    def get(self, request):
        try:
            meetings = ScheduledMeeting.objects.all().order_by('-scheduled_date')

            paginator = GlobalPagination()
            paginated_meetings = paginator.paginate_queryset(
                meetings,
                request
            )

            serializer = ScheduledMeetingSerializer(
                paginated_meetings,
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
            serializer = ScheduledMeetingSerializer(data=request.data)
            if serializer.is_valid():
                meeting_request = serializer.validated_data['request']
                meeting_request.is_scheduled = True
                meeting_request.save()

                scheduled_meeting = serializer.save()

                formatted_date = scheduled_meeting.scheduled_date.strftime("%d-%m-%Y")

                name = scheduled_meeting.request.name
                referral_id = scheduled_meeting.request.referral_id
                department = scheduled_meeting.request.department
                meeting_link = scheduled_meeting.meeting_link
                scheduled_date = formatted_date
                scheduled_time = scheduled_meeting.scheduled_time
                recipient_email = scheduled_meeting.request.email

                subject = "Meeting Scheduled Successfully"
                message = (
                    f"Dear {name},\n\n"
                    f"Your meeting has been scheduled successfully.\n\n"
                    f"Details:\n"
                    f"Name: {name}\n"
                    f"Referral ID: {referral_id}\n"
                    f"Department: {department.name}\n"
                    f"Meeting Link: {meeting_link}\n"
                    f"Scheduled Date: {scheduled_date}\n"
                    f"Scheduled Time: {scheduled_time}\n\n"
                    f"Thank you!"
                )

                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [recipient_email],
                    fail_silently=False,
                )

                return Response(
                    {
                        "message": "Meeting scheduled successfully",
                        "data": serializer.data
                    },
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


# views.py

class ScheduledMeetingDetailView(APIView):
    def get(self, request, scheduled_meeting_id):
        try:
            meeting = get_object_or_404(ScheduledMeeting, scheduled_meeting_id=scheduled_meeting_id)
            serializer = ScheduledMeetingSerializer(meeting)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def put(self, request, scheduled_meeting_id):
        try:
            meeting = get_object_or_404(ScheduledMeeting, scheduled_meeting_id=scheduled_meeting_id)
            old_status = meeting.status  # Save the current status

            serializer = ScheduledMeetingSerializer(meeting, data=request.data, partial=True)
            if serializer.is_valid():
                updated_meeting = serializer.save()
                # Format date as DD-MM-YYYY
                formatted_date = updated_meeting.scheduled_date.strftime("%d-%m-%Y")
                

                # Check if status has changed to 'cancelled' or 'completed'
                new_status = updated_meeting.status
                if old_status != new_status and new_status in ['cancelled', 'completed']:
                    name = updated_meeting.request.name
                    recipient_email = updated_meeting.request.email
                    scheduled_date = formatted_date
                    scheduled_time = updated_meeting.scheduled_time
                    meeting_link = updated_meeting.meeting_link

                    subject = f"Meeting {new_status.capitalize()}"
                    message = (
                        f"Dear {name},\n\n"
                        f"Your scheduled meeting has been {new_status}.\n\n"
                        f"Meeting Details:\n"
                        f"Date: {scheduled_date}\n"
                        f"Time: {scheduled_time}\n"
                        f"Link: {meeting_link if meeting_link else 'N/A'}\n\n"
                        f"Thank you."
                    )

                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [recipient_email],
                        fail_silently=False,
                    )

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, scheduled_meeting_id):
        try:
            meeting = get_object_or_404(ScheduledMeeting, scheduled_meeting_id=scheduled_meeting_id)
            # Unmark the original request as scheduled (optional logic)
            if meeting.request:
                meeting.request.is_scheduled = False
                meeting.request.save()
            meeting.delete()
            return Response({"message": "Scheduled meeting deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




    


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class MeetingRequestsByUserIdAPIView(APIView):
    """
    GET → List meeting requests by user ID (paginated)
    """

    def get(self, request, user_id):
        try:
            meeting_requests = (
                MeetingRequest.objects
                .filter(user_id=user_id)
                .order_by('-created_at')
            )

            paginator = GlobalPagination()
            paginated_requests = paginator.paginate_queryset(
                meeting_requests,
                request
            )

            serializer = MeetingRequestSerializer(
                paginated_requests,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class LeadListCreateView(APIView):

    def get(self, request):
        try:
            leads = Lead.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_leads = paginator.paginate_queryset(
                leads,
                request
            )

            serializer = LeadSerializer(
                paginated_leads,
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
            serializer = LeadSerializer(data=request.data)
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

class LeadDetailView(APIView):
    def get(self, request, id):
        try:
            lead = get_object_or_404(Lead, id=id)
            serializer = LeadSerializer(lead)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            lead = get_object_or_404(Lead, id=id)
            serializer = LeadSerializer(lead, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            lead = get_object_or_404(Lead, id=id)
            lead.delete()
            return Response({"message": "Lead deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class CarouselItemListCreateView(APIView):

    def get(self, request):
        try:
            items = CarouselItem.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_items = paginator.paginate_queryset(items, request)

            serializer = CarouselItemSerializer(paginated_items, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            if 'image' not in request.FILES:
                return Response(
                    {'error': 'Image file is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = CarouselItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class CarouselItemDetailView(APIView):
    def get(self, request, pk):
        try:
            item = get_object_or_404(CarouselItem, pk=pk)
            serializer = CarouselItemSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            item = get_object_or_404(CarouselItem, pk=pk)
            serializer = CarouselItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            item = get_object_or_404(CarouselItem, pk=pk)
            item.delete()
            return Response({'message': 'Carousel item deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class TrainingMaterialListCreateView(APIView):

    def get(self, request):
        try:
            materials = TrainingMaterial.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_materials = paginator.paginate_queryset(materials, request)

            serializer = TrainingMaterialSerializer(
                paginated_materials,
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
            serializer = TrainingMaterialSerializer(data=request.data)
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


class TrainingMaterialDetailView(APIView):
    def get(self, request, id):
        try:
            material = get_object_or_404(TrainingMaterial, id=id)
            serializer = TrainingMaterialSerializer(material)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            material = get_object_or_404(TrainingMaterial, id=id)
            serializer = TrainingMaterialSerializer(material, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            material = get_object_or_404(TrainingMaterial, id=id)
            material.delete()
            return Response({'message': 'Training material deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class HowItWorksListCreateView(APIView):

    def get(self, request):
        try:
            items = HowItWorks.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_items = paginator.paginate_queryset(items, request)

            serializer = HowItWorksSerializer(
                paginated_items,
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
            serializer = HowItWorksSerializer(data=request.data)
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

class HowItWorksDetailView(APIView):
    def get(self, request, id):
        try:
            item = get_object_or_404(HowItWorks, id=id)
            serializer = HowItWorksSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            item = get_object_or_404(HowItWorks, id=id)
            serializer = HowItWorksSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            item = get_object_or_404(HowItWorks, id=id)
            item.delete()
            return Response({'message': 'How It Works entry deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class PhonenumberListCreateView(APIView):

    def get(self, request):
        try:
            phone_numbers = Phonenumber.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_phone_numbers = paginator.paginate_queryset(
                phone_numbers,
                request
            )

            serializer = PhonenumberSerializer(
                paginated_phone_numbers,
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
            serializer = PhonenumberSerializer(data=request.data)
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

class PhonenumberDetailView(APIView):
    def get(self, request, id):
        try:
            phone_number = get_object_or_404(Phonenumber, id=id)
            serializer = PhonenumberSerializer(phone_number)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            phone_number = get_object_or_404(Phonenumber, id=id)
            serializer = PhonenumberSerializer(phone_number, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            phone_number = get_object_or_404(Phonenumber, id=id)
            phone_number.delete()
            return Response({'message': 'Phone number deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# -------------------------------
# Like List & Create API
# -------------------------------

class LikeListCreateView(APIView):
    """
    GET  → List all likes (paginated)
    POST → Create a new like
    """

    def get(self, request):
        try:
            likes = Like.objects.all().order_by('-created_at')

            paginator = GlobalPagination()
            paginated_likes = paginator.paginate_queryset(
                likes,
                request
            )

            serializer = LikeSerializer(
                paginated_likes,
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
            serializer = LikeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Like created successfully",
                        "data": serializer.data
                    },
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


# -------------------------------
# Like Detail (GET, PUT, DELETE)
# -------------------------------
class LikeDetailView(APIView):
    """
    GET    → Retrieve a single like
    PUT    → Update like
    DELETE → Remove like
    """
    def get(self, request, like_id):
        try:
            like = get_object_or_404(Like, id=like_id)
            serializer = LikeSerializer(like)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, like_id):
        try:
            like = get_object_or_404(Like, id=like_id)
            serializer = LikeSerializer(like, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Like updated successfully", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, like_id):
        try:
            like = get_object_or_404(Like, id=like_id)
            like.delete()
            return Response({"message": "Like deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# -------------------------------
# Wishlist List & Create API
# -------------------------------


class WishlistListCreateView(APIView):
    """
    GET  → List all wishlists (paginated)
    POST → Create a new wishlist
    """

    def get(self, request):
        try:
            wishlists = Wishlist.objects.all().order_by('-created_at')

            paginator = GlobalPagination()
            paginated_wishlists = paginator.paginate_queryset(
                wishlists,
                request
            )

            serializer = WishlistSerializer(
                paginated_wishlists,
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
            serializer = WishlistSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Wishlist item created successfully",
                        "data": serializer.data
                    },
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


# -------------------------------
# Wishlist Detail (GET, PUT, DELETE)
# -------------------------------
class WishlistDetailView(APIView):
    """
    GET    → Retrieve a single wishlist item
    PUT    → Update wishlist
    DELETE → Remove wishlist
    """
    def get(self, request, wishlist_id):
        try:
            wishlist = get_object_or_404(Wishlist, id=wishlist_id)
            serializer = WishlistSerializer(wishlist)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, wishlist_id):
        try:
            wishlist = get_object_or_404(Wishlist, id=wishlist_id)
            serializer = WishlistSerializer(wishlist, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Wishlist updated successfully", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, wishlist_id):
        try:
            wishlist = get_object_or_404(Wishlist, id=wishlist_id)
            wishlist.delete()
            return Response({"message": "Wishlist deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









class WishlistByUserAPIView(APIView):
    """
    GET → Retrieve all wishlist items for a given user (paginated)
    """

    def get(self, request, user_id):
        try:
            wishlists = (
                Wishlist.objects
                .filter(user_id=user_id)
                .order_by('-created_at')
            )

            paginator = GlobalPagination()
            paginated_wishlists = paginator.paginate_queryset(
                wishlists,
                request
            )

            serializer = WishlistSerializer(
                paginated_wishlists,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



from django.core.mail import send_mail
from django.conf import settings

def get_bot_response(message, is_other=False):
    message = message.lower().strip()

    # ✅ Step 1: If user is replying to "Other"
    if is_other:
        send_mail(
            subject="Chatbot Query from User",
            message=f"User Query: {message}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["shrirajteam@gmail.com"],
            fail_silently=False,
        )
        return {"response": "Thank you! Your question has been sent to our support team."}

    # ✅ Step 2: When user types hi/hello → show menu
    if ChatKeyword.objects.filter(keyword__iexact=message).exists():
        responses = ChatResponse.objects.all().order_by("id")
        questions = [{"id": r.id, "question": r.question} for r in responses]
        return {"response": "Please choose an option:", "questions": questions}

    # ✅ Step 3: When user enters a number (question ID)
    if message.isdigit():
        try:
            response = ChatResponse.objects.get(id=int(message))
            if "other" in response.question.lower():
                return {
                    "response": "Please type your question, and we'll send it to our support team.",
                    "is_other": True,  # frontend should set is_other=True for next message
                }
            return {"response": response.answer}
        except ChatResponse.DoesNotExist:
            return {"response": "Invalid option. Please choose a valid question number."}

    # ✅ Step 4: Default fallback
    return {"response": "Sorry, I didn't understand that. Type 'hi' or 'hello' to start."}



# ✅ Chatbot API
class ChatBotAPIView(APIView):
    def post(self, request):
        message = request.data.get("message", "")
        is_other = request.data.get("is_other", False)

        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = get_bot_response(message, is_other)
        return Response(response_data, status=status.HTTP_200_OK)


# ✅ Chat Responses List + Create

class ChatResponseListCreateAPIView(APIView):

    def get(self, request):
        try:
            responses = ChatResponse.objects.all().order_by('id')

            paginator = GlobalPagination()
            paginated_responses = paginator.paginate_queryset(
                responses,
                request
            )

            serializer = ChatResponseSerializer(
                paginated_responses,
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
            serializer = ChatResponseSerializer(data=request.data)
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

# ✅ Chat Response Retrieve + Update + Delete
class ChatResponseDetailView(APIView):
    def get(self, request, pk):
        response = get_object_or_404(ChatResponse, pk=pk)
        serializer = ChatResponseSerializer(response)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        response = get_object_or_404(ChatResponse, pk=pk)
        serializer = ChatResponseSerializer(response, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Chat response updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        response = get_object_or_404(ChatResponse, pk=pk)
        response.delete()
        return Response(
            {"message": "Chat response deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )



# API to add chatbot keywords


class ChatKeywordListCreateAPIView(APIView):

    def get(self, request):
        try:
            keywords = ChatKeyword.objects.all().order_by('id')

            paginator = GlobalPagination()
            paginated_keywords = paginator.paginate_queryset(
                keywords,
                request
            )

            serializer = ChatKeywordSerializer(
                paginated_keywords,
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
            serializer = ChatKeywordSerializer(data=request.data)
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

# -------------------------------
# Site Visit List & Create API
# -------------------------------



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SiteVisitListCreateView(APIView):
    """
    GET  → List all site visits (paginated)
    POST → Create a new site visit
    """

    def get(self, request):
        try:
            site_visits = SiteVisit.objects.all().order_by('-date', '-time')

            paginator = GlobalPagination()
            paginated_site_visits = paginator.paginate_queryset(
                site_visits,
                request
            )

            serializer = SiteVisitSerializer(
                paginated_site_visits,
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
            serializer = SiteVisitSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Site visit created successfully",
                        "data": serializer.data
                    },
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

# -------------------------------
# Site Visit Detail (GET, PUT, DELETE)
# -------------------------------
class SiteVisitDetailView(APIView):
    """
    GET    → Retrieve a single site visit
    PUT    → Update site visit details
    DELETE → Remove site visit
    """
    def get(self, request, visit_id):
        try:
            site_visit = get_object_or_404(SiteVisit, id=visit_id)
            serializer = SiteVisitSerializer(site_visit)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, visit_id):
        try:
            site_visit = get_object_or_404(SiteVisit, id=visit_id)
            serializer = SiteVisitSerializer(site_visit, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Site visit updated successfully", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, visit_id):
        try:
            site_visit = get_object_or_404(SiteVisit, id=visit_id)
            site_visit.delete()
            return Response(
                {"message": "Site visit deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class SiteVisitsByUserView(APIView):
    """
    GET → List site visits for a given user (paginated)
    """

    def get(self, request, id):
        try:
            site_visits = SiteVisit.objects.filter(user_id=id).order_by('-date', '-time')

            paginator = GlobalPagination()
            paginated_visits = paginator.paginate_queryset(site_visits, request)

            serializer = SiteVisitSerializer(paginated_visits, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )








class ReferralPrefixListCreateView(APIView):
    def get(self, request):
        prefixes = ReferralPrefix.objects.all().order_by('-created_at')
        serializer = ReferralPrefixSerializer(prefixes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReferralPrefixSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ReferralPrefixDetailView(APIView):
    def get_object(self, id):
        return get_object_or_404(ReferralPrefix, id=id)

    def get(self, request, id):
        prefix = self.get_object(id)
        serializer = ReferralPrefixSerializer(prefix)
        return Response(serializer.data)

    def put(self, request, id):
        prefix = self.get_object(id)
        serializer = ReferralPrefixSerializer(prefix, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        prefix = self.get_object(id)
        prefix.delete()
        return Response({"message": "Deleted successfully"}, status=204)












class CartListCreateView(APIView):

    # 🔹 GET ALL CART ITEMS (ADMIN / INTERNAL)
    def get(self, request):
        try:
            carts = Cart.objects.select_related(
                'user', 'product', 'property_item'
            ).all()

            serializer = CartSerializer(carts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔹 ADD TO CART
    def post(self, request):
        try:
            user_id = request.data.get("user")
            product_id = request.data.get("product")
            property_id = request.data.get("property_item")
            quantity = int(request.data.get("quantity", 1))

            if not user_id:
                return Response({"error": "user is required"}, status=400)

            # PRODUCT CART
            if product_id:
                product = get_object_or_404(Product, id=product_id)

                if quantity < 1:
                    return Response({"error": "Quantity must be at least 1"}, status=400)

                if product.available_qty < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)

                cart_item, created = Cart.objects.get_or_create(
                    user_id=user_id,
                    product=product,
                    defaults={"quantity": quantity}
                )

                if not created:
                    new_qty = cart_item.quantity + quantity
                    if product.available_qty < new_qty:
                        return Response({"error": "Insufficient stock"}, status=400)

                    cart_item.quantity = new_qty
                    cart_item.save()

            # PROPERTY CART
            elif property_id:
                property_item = get_object_or_404(Property, id=property_id)

                if Cart.objects.filter(user_id=user_id, property_item=property_item).exists():
                    return Response(
                        {"error": "Property already added to cart"},
                        status=400
                    )

                Cart.objects.create(
                    user_id=user_id,
                    property_item=property_item,
                    quantity=1
                )

            else:
                return Response(
                    {"error": "Either product or property_item is required"},
                    status=400
                )

            return Response(
                {"message": "Item added to cart successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartByUserAPIView(APIView):

    

    def get(self, request, user_id):
        try:
            cart_items = Cart.objects.filter(
                user_id=user_id
            ).select_related('product', 'property_item')

            serializer = CartSerializer(cart_items, many=True)

            total_amount = sum(item.subtotal for item in cart_items)

            return Response({
                "items": serializer.data,
                "total_amount": total_amount
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CartDetailView(APIView):
    def get(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)

            quantity = int(request.data.get("quantity", cart_item.quantity))

            if cart_item.product:
                if quantity < 1:
                    return Response({"error": "Quantity must be at least 1"}, status=400)

                if cart_item.product.available_qty < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)

                cart_item.quantity = quantity
                cart_item.save()

            return Response(
                {"message": "Cart updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)
            cart_item.delete()
            return Response(
                {"message": "Cart item removed"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)









