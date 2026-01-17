import django_filters
from django.db.models import Q, Min, Max
from .models import Business, Product, ProductVariant
from .models import *



class BusinessFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')

    # Seller
    user_id = django_filters.NumberFilter(field_name='user_id')

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
    # Filter by category slug (strict)
    category_slug = django_filters.CharFilter(
        field_name='categories__slug',
        lookup_expr='iexact'
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

    search = django_filters.CharFilter(method='filter_search')

    business = django_filters.NumberFilter(field_name='business_id')
    business_slug = django_filters.CharFilter(field_name='business__slug', lookup_expr='iexact')

    # Filter by product category slug
    #category_slug = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    #category_slug = django_filters.CharFilter(method='filter_category_slug')


    category_slug = django_filters.CharFilter(method='filter_category_slug')
    category_id = django_filters.NumberFilter(method='filter_category_id')

    def filter_category_slug(self, queryset, name, value):
        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()

        return self._apply_category_filter(queryset, category)


    def filter_category_id(self, queryset, name, value):
        try:
            category = Category.objects.get(pk=value)
        except Category.DoesNotExist:
            return queryset.none()

        return self._apply_category_filter(queryset, category)

    def _apply_category_filter(self, queryset, category):

        # GLOBAL
        if category.level == 'global':
            business_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)
            product_ids = Category.objects.filter(parent__in=business_ids).values_list('category_id', flat=True)
            return queryset.filter(category_id__in=list(product_ids)).distinct()

        # BUSINESS
        if category.level == 'business':
            product_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)
            return queryset.filter(category_id__in=list(product_ids)).distinct()

        # PRODUCT
        if category.level == 'product':
            return queryset.filter(category_id=category.category_id).distinct()

        return queryset


    # Filter by business allowed category id
    business_category = django_filters.NumberFilter(method='filter_business_category')

    # Filter by business allowed category slug
    business_category_slug = django_filters.CharFilter(method='filter_business_category_slug')

    category = django_filters.NumberFilter(field_name='category_id')
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='iexact')

    verification_status = django_filters.CharFilter(field_name='verification_status')
    variant_verification_status = django_filters.CharFilter(method='filter_variant_status')

    is_active = django_filters.BooleanFilter(field_name='is_active')
    has_variants = django_filters.BooleanFilter(field_name='has_variants')

    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')

    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    price_min = django_filters.NumberFilter(field_name='variants__selling_price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='variants__selling_price', lookup_expr='lte')

    in_stock = django_filters.BooleanFilter(method='filter_stock')
    has_offer = django_filters.BooleanFilter(method='filter_offer')

    attributes = django_filters.CharFilter(method='filter_attributes')

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

    # ---------- Custom Methods ----------
    

    def filter_variant_status(self, queryset, name, value):
        qs = queryset.filter(
            variants__verification_status=value
        ).distinct()

        # If no matching verified variants exist → return empty queryset
        if not qs.exists():
            return queryset.none()

        return qs



    def filter_business_category(self, queryset, name, value):
        return queryset.filter(
            business__categories__category_id=value
        ).distinct()

    def filter_business_category_slug(self, queryset, name, value):
        return queryset.filter(
            business__categories__slug__iexact=value
        ).distinct()

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

    @property
    def qs(self):
        return super().qs.annotate(
            min_price=Min('variants__selling_price'),
            max_price=Max('variants__selling_price')
        )




