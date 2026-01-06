import threading
import time
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import localtime


def meeting_reminder_loop():
    from .models import ScheduledMeeting
    #print("✅ Meeting reminder thread started.")

    while True:
        try:
            now = localtime()  # Ensure timezone-aware now
            #reminder_start = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
            reminder_start = (now + timedelta(minutes=30)).replace(second=0, microsecond=0)
            reminder_end = reminder_start + timedelta(minutes=1)
            #print(f"⏰ Checking meetings scheduled between {reminder_start.time()} and {reminder_end.time()} on {reminder_start.date()}")

            meetings = ScheduledMeeting.objects.filter(
                scheduled_date=reminder_start.date(),
                scheduled_time__gte=reminder_start.time(),
                scheduled_time__lt=reminder_end.time(),
                status='scheduled',
                reminder_sent=False
            )

            #print(f"📅 Meetings found: {meetings.count()}")
            for meeting in meetings:
                name = meeting.name or getattr(meeting.request, 'name', 'User')
                email = meeting.email or getattr(meeting.request, 'email', None)
                referral_id = meeting.referral_id or getattr(meeting.request, 'referral_id', '')
                profile_type = meeting.profile_type or getattr(meeting.request, 'profile_type', '')

                if not email:
                    #print(f"⚠️ No email for meeting {meeting.id}, skipping.")
                    continue

                subject = "Upcoming Meeting Reminder"
                message = (
                    f"Dear {name},\n\n"
                    f"This is a reminder that your meeting is scheduled in 5 minutes.\n\n"
                    f"Details:\n"
                    f"Name: {name}\n"
                    f"Referral ID: {referral_id}\n"
                    f"Profile Type: {profile_type}\n"
                    f"Meeting Link: {meeting.meeting_link}\n"
                    f"Scheduled Date: {meeting.scheduled_date}\n"
                    f"Scheduled Time: {meeting.scheduled_time}\n\n"
                    f"Thank you!"
                )
                try:
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=False)
                    #print(f"✅ Email sent to {email}")
                    meeting.reminder_sent = True
                    meeting.save()
                except Exception as e:
                    print(f"❌ Error sending to {email}: {e}")

        except Exception as e:
            print(f"❌ Error in reminder loop: {e}")

        time.sleep(60)



def delayed_start():
    reminder_thread = threading.Thread(target=meeting_reminder_loop)
    reminder_thread.daemon = True
    reminder_thread.start()
    #print("🧵 Reminder thread started after delay.")


def start_thread():
    threading.Timer(5, delayed_start).start()  # 5-second delay before starting the loop
