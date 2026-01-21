# from django.apps import AppConfig


# class SubscriptionConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'subscription'

#     def ready(self):
#         from . import tasks
#         tasks.start_thread()


import sys
from django.apps import AppConfig
import os

class SubscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscription'

    def ready(self):
        # Prevent thread from running twice due to autoreload
        if os.environ.get('RUN_MAIN') == 'true':
            from .tasks import start_thread
            start_thread()


    