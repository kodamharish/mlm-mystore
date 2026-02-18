# import threading
# import time
# from datetime import date
# from .models import Subscription
# from users.models import *


# def update_subscription_status():
#     from .models import Subscription
#     from users.models import User  # or specific model used

#     while True:
#         try:
#             today = date.today()
#             subscriptions = Subscription.objects.filter(subscription_status='paid')

#             for sub in subscriptions:
#                 if sub.subscription_end_date <= today:
#                     sub.subscription_status = "unpaid"
#                     sub.save()
#                     user = sub.user_id
#                     user.status = 'inactive'
#                     user.save()

#         except Exception as e:
#             print(f"[{date.today()}] Error in update_subscription_status: {e}")

#         time.sleep(86400)  # 24 hours
#         #time.sleep(10)  # For testing


# def start_thread():
#     print("Subscription thread starting...")  # ✅ Debug print
#     printer_thread = threading.Thread(target=update_subscription_status)
#     printer_thread.daemon = True
#     printer_thread.start()



import threading
import time
from django.utils import timezone
from subscription.models import Subscription


def update_subscription_status():
    while True:
        try:
            now = timezone.now()  # timezone-aware datetime

            # Fetch subscriptions that have expired
            subscriptions = Subscription.objects.filter(
                subscription_status='paid',
                subscription_end_datetime__lte=now
            )

            for sub in subscriptions:
                sub.subscription_status = 'unpaid'
                sub.save(update_fields=['subscription_status'])

                user = sub.user_id
                user.status = 'inactive'
                user.save(update_fields=['status'])

            print(f"[{now}] Expired subscriptions processed: {subscriptions.count()}")

        except Exception as e:
            print(f"[{timezone.now()}] Error in update_subscription_status: {e}")

        # Sleep for 24 hours
        #time.sleep(86400)
        # For testing:
        time.sleep(60)


def start_thread():
    print("Subscription thread starting...")
    subscription_thread = threading.Thread(target=update_subscription_status)
    subscription_thread.daemon = True
    subscription_thread.start()

