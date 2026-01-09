# import django_filters
# from django.db.models import Q
# from .models import *


# class BusinessFilter(django_filters.FilterSet):

#     search = django_filters.CharFilter(method='filter_search')

#     business_type = django_filters.CharFilter(field_name='business_type')
#     verification_status = django_filters.CharFilter(field_name='verification_status')
#     is_active = django_filters.BooleanFilter(field_name='is_active')

#     category = django_filters.NumberFilter(field_name='categories__id')

#     city = django_filters.CharFilter(field_name='city', lookup_expr='iexact')
#     state = django_filters.CharFilter(field_name='state', lookup_expr='iexact')
#     country = django_filters.CharFilter(field_name='country', lookup_expr='iexact')

#     rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
#     rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

#     class Meta:
#         model = Business
#         fields = []

#     def filter_search(self, queryset, name, value):
#         return queryset.filter(
#             Q(business_name__icontains=value) |
#             Q(legal_name__icontains=value) |
#             Q(gst_number__icontains=value) |
#             Q(pan_number__icontains=value)
#         ).distinct()


# class ProductFilter(django_filters.FilterSet):

#     # 🔍 Search
#     search = django_filters.CharFilter(method='filter_search')

#     # 🏪 Product-level
#     business = django_filters.NumberFilter(field_name='business_id')
#     category = django_filters.NumberFilter(field_name='category_id')
#     brand = django_filters.CharFilter(field_name='brand', lookup_expr='iexact')

#     verification_status = django_filters.CharFilter(field_name='verification_status')
#     is_active = django_filters.BooleanFilter(field_name='is_active')
#     has_variants = django_filters.BooleanFilter(field_name='has_variants')

#     rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
#     rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

#     created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
#     created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

#     # 💰 VARIANT-LEVEL (NESTED)
#     price_min = django_filters.NumberFilter(
#         field_name='variants__selling_price',
#         lookup_expr='gte'
#     )
#     price_max = django_filters.NumberFilter(
#         field_name='variants__selling_price',
#         lookup_expr='lte'
#     )

#     in_stock = django_filters.BooleanFilter(method='filter_stock')
#     has_offer = django_filters.BooleanFilter(method='filter_offer')

#     # 🧬 JSON ATTRIBUTES (Amazon-style)
#     attributes = django_filters.CharFilter(method='filter_attributes')

#     class Meta:
#         model = Product
#         fields = []

#     # --------------------------
#     # Custom Filters
#     # --------------------------

#     def filter_search(self, queryset, name, value):
#         return queryset.filter(
#             Q(product_name__icontains=value) |
#             Q(brand__icontains=value) |
#             Q(model_no__icontains=value)
#         ).distinct()

#     def filter_stock(self, queryset, name, value):
#         if value:
#             return queryset.filter(variants__stock__gt=0).distinct()
#         return queryset.filter(variants__stock=0).distinct()

#     def filter_offer(self, queryset, name, value):
#         if value:
#             return queryset.filter(variants__offer__isnull=False).distinct()
#         return queryset.filter(variants__offer__isnull=True).distinct()

#     def filter_attributes(self, queryset, name, value):
#         """
#         Usage:
#         ?attributes=color:Black,size:L
#         """
#         try:
#             filters = value.split(',')
#             for f in filters:
#                 key, val = f.split(':')
#                 queryset = queryset.filter(attributes__contains={key: val})
#         except ValueError:
#             pass
#         return queryset.distinct()


# class ProductVariantFilter(django_filters.FilterSet):

#     sku = django_filters.CharFilter(field_name='sku', lookup_expr='icontains')

#     price_min = django_filters.NumberFilter(field_name='selling_price', lookup_expr='gte')
#     price_max = django_filters.NumberFilter(field_name='selling_price', lookup_expr='lte')

#     in_stock = django_filters.BooleanFilter(method='filter_stock')

#     class Meta:
#         model = ProductVariant
#         fields = []

#     def filter_stock(self, queryset, name, value):
#         if value:
#             return queryset.filter(stock__gt=0)
#         return queryset.filter(stock=0)



import django_filters
from django.db.models import Q, Min, Max
from .models import Business, Product, ProductVariant





class BusinessFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')

    # Seller
    user = django_filters.NumberFilter(field_name='user_id')

    business_type = django_filters.CharFilter(field_name='business_type')
    verification_status = django_filters.CharFilter(field_name='verification_status')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    #category = django_filters.NumberFilter(field_name='categories__id')

    # Filter by category_id
    category = django_filters.NumberFilter(field_name='categories__id')

    #Filter by category name exact match
    # category_name = django_filters.CharFilter(
    # field_name='categories__name',
    # lookup_expr='iexact'
    # )


    # Filter by category name patial match
    category_name = django_filters.CharFilter(
        field_name='categories__name',
        lookup_expr='icontains'
    )

    category_level = django_filters.CharFilter(
    field_name='categories__level',
    lookup_expr='iexact'
    )


    city = django_filters.CharFilter(field_name='city', lookup_expr='iexact')
    state = django_filters.CharFilter(field_name='state', lookup_expr='iexact')
    country = django_filters.CharFilter(field_name='country', lookup_expr='iexact')

    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

    # 🔥 ORDERING
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'latest'),
            ('rating', 'rating'),
        )
    )

    class Meta:
        model = Business
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(business_name__icontains=value) |
            Q(legal_name__icontains=value) |
            Q(gst_number__icontains=value) |
            Q(pan_number__icontains=value)
        ).distinct()

class ProductFilter(django_filters.FilterSet):

    # 🔍 Search
    search = django_filters.CharFilter(method='filter_search')

    # Seller / Business
    business = django_filters.NumberFilter(field_name='business_id')

    category = django_filters.NumberFilter(field_name='category_id')
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='iexact')

    verification_status = django_filters.CharFilter(field_name='verification_status')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    has_variants = django_filters.BooleanFilter(field_name='has_variants')

    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    # 💰 Variant price filtering
    price_min = django_filters.NumberFilter(
        field_name='variants__selling_price',
        lookup_expr='gte'
    )
    price_max = django_filters.NumberFilter(
        field_name='variants__selling_price',
        lookup_expr='lte'
    )

    in_stock = django_filters.BooleanFilter(method='filter_stock')
    has_offer = django_filters.BooleanFilter(method='filter_offer')

    # 🧬 Attributes
    attributes = django_filters.CharFilter(method='filter_attributes')

    # 🔥 ORDERING (AMAZON STYLE)
    ordering = django_filters.OrderingFilter(
        fields=(
            ('min_price', 'price'),
            ('created_at', 'latest'),
            ('rating', 'rating'),
        )
    )

    class Meta:
        model = Product
        fields = []

    # ---------- Custom Filters ----------

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(product_name__icontains=value) |
            Q(brand__icontains=value) |
            Q(model_no__icontains=value)
        ).distinct()

    def filter_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock__gt=0).distinct()
        return queryset.filter(variants__stock=0).distinct()

    def filter_offer(self, queryset, name, value):
        if value:
            return queryset.filter(variants__offer__isnull=False).distinct()
        return queryset.filter(variants__offer__isnull=True).distinct()

    def filter_attributes(self, queryset, name, value):
        try:
            for f in value.split(','):
                key, val = f.split(':')
                queryset = queryset.filter(attributes__contains={key: val})
        except ValueError:
            pass
        return queryset.distinct()

    # 🔥 IMPORTANT: annotate price before filtering
    @property
    def qs(self):
        return super().qs.annotate(
            min_price=Min('variants__selling_price'),
            max_price=Max('variants__selling_price')
        )
