import django_filters
from django.db.models import Q
from .models import User


class UserFilter(django_filters.FilterSet):

    # -------------------------------------------------
    # 🔍 Keyword Search (Global)
    # -------------------------------------------------
    keyword = django_filters.CharFilter(method='filter_keyword')
    search = django_filters.CharFilter(method='filter_keyword')

    # -------------------------------------------------
    # Role
    # -------------------------------------------------
    role = django_filters.CharFilter(method='filter_role')

    # -------------------------------------------------
    # Status & Verification
    # -------------------------------------------------
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='iexact'
    )

    kyc_status = django_filters.CharFilter(
        field_name='kyc_status',
        lookup_expr='iexact'
    )

    # -------------------------------------------------
    # Referral
    # -------------------------------------------------
    referral_id = django_filters.CharFilter(
        field_name='referral_id',
        lookup_expr='iexact'
    )

    referred_by = django_filters.CharFilter(
        field_name='referred_by',
        lookup_expr='iexact'
    )

    # -------------------------------------------------
    # Personal Identifiers (EXPLICIT)
    # -------------------------------------------------
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='iexact'
    )

    phone_number = django_filters.CharFilter(
        field_name='phone_number',
        lookup_expr='iexact'
    )

    # -------------------------------------------------
    # Location
    # -------------------------------------------------
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains'
    )

    state = django_filters.CharFilter(
        field_name='state',
        lookup_expr='icontains'
    )

    country = django_filters.CharFilter(
        field_name='country',
        lookup_expr='icontains'
    )

    # -------------------------------------------------
    # Level
    # -------------------------------------------------
    level_no = django_filters.NumberFilter()

    # -------------------------------------------------
    # Date Filter
    # -------------------------------------------------
    created_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = User
        fields = []  # Explicit filters only

    # -------------------------------------------------
    # Custom Filter Methods
    # -------------------------------------------------
    def filter_keyword(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(phone_number__icontains=value) |
            Q(referral_id__icontains=value) |
            Q(referred_by__icontains=value) |
            Q(city__icontains=value) |
            Q(state__icontains=value)
        )

    def filter_role(self, queryset, name, value):
        return queryset.filter(
            roles__role_name__iexact=value
        )
