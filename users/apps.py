# from django.apps import AppConfig


# class UsersConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'users'


from django.apps import AppConfig
import sys
import os


class SubscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        #if 'runserver' in sys.argv:
        if os.environ.get('RUN_MAIN') == 'true':
            print("🔥 Starting meeting reminder thread")
            from .meeting_reminder import start_thread
            start_thread()
