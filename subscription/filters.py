# subscriptions/filters.py
import django_filters
from django.db.models import Q
from .models import Subscription

class SubscriptionFilter(django_filters.FilterSet):

    # -------------------------------------------------
    # 🔍 GLOBAL SEARCH
    # -------------------------------------------------
    search = django_filters.CharFilter(method="filter_search")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user_id__email__icontains=value) |
            Q(user_id__first_name__icontains=value) |
            Q(user_id__last_name__icontains=value) |
            Q(subscription_variant__plan_id__plan_name__icontains=value) |
            Q(subscription_status__icontains=value)
        )

    # -------------------------------------------------
    # USER FILTERS
    # -------------------------------------------------
    user_id = django_filters.NumberFilter(field_name="user_id__id")

    # -------------------------------------------------
    # PLAN FILTERS
    # -------------------------------------------------
    plan_name = django_filters.CharFilter(
        field_name="subscription_variant__plan_id__plan_name",
        lookup_expr="icontains"
    )

    user_type = django_filters.CharFilter(
        field_name="subscription_variant__plan_id__user_type",
        lookup_expr="iexact"
    )

    # -------------------------------------------------
    # VARIANT FILTERS
    # -------------------------------------------------
    duration_in_days = django_filters.NumberFilter(
        field_name="subscription_variant__duration_in_days"
    )

    min_price = django_filters.NumberFilter(
        field_name="subscription_variant__price", lookup_expr="gte"
    )
    max_price = django_filters.NumberFilter(
        field_name="subscription_variant__price", lookup_expr="lte"
    )

    # -------------------------------------------------
    # STATUS & DATE
    # -------------------------------------------------
    subscription_status = django_filters.CharFilter(lookup_expr="iexact")

    start_date_from = django_filters.DateFilter(
        field_name="subscription_start_date", lookup_expr="gte"
    )
    start_date_to = django_filters.DateFilter(
        field_name="subscription_start_date", lookup_expr="lte"
    )

    class Meta:
        model = Subscription
        fields = []
