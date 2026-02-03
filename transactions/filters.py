import django_filters
from .models import Transaction



class TransactionFilter(django_filters.FilterSet):
    # Direct fields
    user_id = django_filters.NumberFilter(field_name="user_id__user_id")
    property_id = django_filters.NumberFilter(field_name="property_id__property_id")
    order_id = django_filters.NumberFilter(field_name="order__order_id")

    transaction_for = django_filters.CharFilter(field_name="transaction_for")
    payment_type = django_filters.CharFilter(field_name="payment_type")
    payment_mode = django_filters.CharFilter(field_name="payment_mode")
    status = django_filters.CharFilter(field_name="status")

    # 🔥 ROLE FILTER (via User → Role)
    role_id = django_filters.NumberFilter(
        field_name="user_id__roles__role_id"
    )

    role_name = django_filters.CharFilter(
        field_name="user_id__roles__role_name",
        lookup_expr="iexact"
    )

    # Amount filters
    min_amount = django_filters.NumberFilter(
        field_name="paid_amount", lookup_expr="gte"
    )
    max_amount = django_filters.NumberFilter(
        field_name="paid_amount", lookup_expr="lte"
    )

    # Date filters
    start_date = django_filters.DateFilter(
        field_name="transaction_date", lookup_expr="date__gte"
    )
    end_date = django_filters.DateFilter(
        field_name="transaction_date", lookup_expr="date__lte"
    )

    class Meta:
        model = Transaction
        fields = [
            "user_id",
            "property_id",
            "order_id",
            "transaction_for",
            "payment_type",
            "payment_mode",
            "status",
            "role_id",
            "role_name",
        ]




import django_filters
from .models import Order, OrderItem


class OrderFilter(django_filters.FilterSet):
    user_id = django_filters.NumberFilter(field_name="user__user_id")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")

    min_amount = django_filters.NumberFilter(
        field_name="total_amount", lookup_expr="gte"
    )
    max_amount = django_filters.NumberFilter(
        field_name="total_amount", lookup_expr="lte"
    )

    start_date = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    end_date = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Order
        fields = [
            "user_id",
            "status",
        ]


class OrderItemFilter(django_filters.FilterSet):
    order_id = django_filters.NumberFilter(field_name="order__order_id")
    variant_id = django_filters.NumberFilter(field_name="variant__id")
    property_id = django_filters.NumberFilter(field_name="property_item__property_id")

    class Meta:
        model = OrderItem
        fields = [
            "order_id",
            "variant_id",
            "property_id",
        ]

