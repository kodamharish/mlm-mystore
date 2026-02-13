import django_filters
from django.db.models import Q
from .models import *
from users.models import User


class PropertyFilter(django_filters.FilterSet):

    # -------------------------------------------------
    # Keyword Search
    # -------------------------------------------------
    keyword = django_filters.CharFilter(method='filter_keyword')
    search = django_filters.CharFilter(method='filter_keyword')

    # -------------------------------------------------
    # Category & Property Type
    # -------------------------------------------------
    category = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='iexact'
    )

    property_type = django_filters.CharFilter(
        field_name='property_type__name',
        lookup_expr='iexact'
    )

    # Alias for `property_type`
    type = django_filters.CharFilter(
        field_name='property_type__name',
        lookup_expr='iexact'
    )

    # -------------------------------------------------
    # Looking To (Sell / Rent / Lease)
    # -------------------------------------------------
    looking_to = django_filters.CharFilter(
        field_name='looking_to',
        lookup_expr='iexact'
    )

    # -------------------------------------------------
    # Status / Approval / Verification
    # -------------------------------------------------
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    approval_status = django_filters.CharFilter(field_name='approval_status', lookup_expr='iexact')
    verification_status = django_filters.CharFilter(field_name='verification_status', lookup_expr='iexact')

    # -------------------------------------------------
    # USER-BASED FILTERS
    # -------------------------------------------------
    user_id = django_filters.NumberFilter(field_name='user_id')
    added_by = django_filters.NumberFilter(field_name='added_by')
    owner = django_filters.NumberFilter(field_name='owner')

    # -------------------------------------------------
    # ROLE-BASED FILTER (NEW)
    # -------------------------------------------------
    role = django_filters.CharFilter(method='filter_role')

    # multiple role support → role=Broker,Owner
    def filter_role(self, queryset, name, value):
        roles = [r.strip() for r in value.split(',')]

        users = User.objects.filter(roles__role_name__in=roles)
        return queryset.filter(user_id__in=users).distinct()

    # -------------------------------------------------
    # Facing & Furnishing
    # -------------------------------------------------
    facing = django_filters.CharFilter(field_name='facing', lookup_expr='iexact')
    furnishing_status = django_filters.CharFilter(field_name='furnishing_status', lookup_expr='iexact')

    # -------------------------------------------------
    # Numeric Filters
    # -------------------------------------------------
    number_of_bedrooms = django_filters.NumberFilter()
    number_of_floors = django_filters.NumberFilter()
    floor = django_filters.NumberFilter()

    # -------------------------------------------------
    # Dimension Filters
    # -------------------------------------------------
    length_ft = django_filters.RangeFilter()
    breadth_ft = django_filters.RangeFilter()

    # -------------------------------------------------
    # PRICE FILTERS (ALL SUPPORTED)
    # -------------------------------------------------
    total_property_value = django_filters.RangeFilter()

    price_min = django_filters.NumberFilter(
        field_name='total_property_value',
        lookup_expr='gte'
    )
    price_max = django_filters.NumberFilter(
        field_name='total_property_value',
        lookup_expr='lte'
    )

    price_range = django_filters.CharFilter(method='filter_price_range')

    def filter_price_range(self, queryset, name, value):
        ranges = {
            'under_10l': (None, 10_00_000),
            '10l_25l': (10_00_000, 25_00_000),
            '25l_50l': (25_00_000, 50_00_000),
            '50l_1cr': (50_00_000, 1_00_00_000),
            '1cr_5cr': (1_00_00_000, 5_00_00_000),
            'above_5cr': (5_00_00_000, None),
        }

        if value not in ranges:
            return queryset

        min_price, max_price = ranges[value]
        queryset = queryset.exclude(total_property_value__isnull=True)

        if min_price and max_price:
            return queryset.filter(
                total_property_value__gte=min_price,
                total_property_value__lt=max_price
            )

        if min_price:
            return queryset.filter(total_property_value__gte=min_price)

        if max_price:
            return queryset.filter(total_property_value__lt=max_price)

        return queryset

    # -------------------------------------------------
    # Amenities Filter
    # -------------------------------------------------
    amenities = django_filters.CharFilter(method='filter_amenities')

    def filter_amenities(self, queryset, name, value):
        return queryset.filter(
            amenities__name__in=[a.strip() for a in value.split(',')]
        ).distinct()

    # -------------------------------------------------
    # Keyword Matching Filter
    # -------------------------------------------------
    def filter_keyword(self, queryset, name, value):
        return queryset.filter(
            Q(property_title__icontains=value) |
            Q(description__icontains=value) |
            Q(city__icontains=value) |
            Q(state__icontains=value) |
            Q(address__icontains=value)
        )

    class Meta:
        model = Property
        fields = []
