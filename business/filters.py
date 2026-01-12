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
from .models import *





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


class ProductFilter_old1(django_filters.FilterSet):

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

        # 🔹 GLOBAL LEVEL
        if category.level == 'global':
            business_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)
            product_ids = Category.objects.filter(parent__in=business_ids).values_list('category_id', flat=True)

            return queryset.filter(
                Q(business__categories__category_id__in=list(business_ids)) |
                Q(category_id__in=list(product_ids))
            ).distinct()

        # 🔹 BUSINESS LEVEL
        if category.level == 'business':
            product_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)

            return queryset.filter(
                Q(business__categories__category_id=category.category_id) |
                Q(category_id__in=list(product_ids))
            ).distinct()

        # 🔹 PRODUCT LEVEL
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

    def filter_category_slug1(self, queryset, name, value):
        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()

        # If category is BUSINESS level → match all product-level children
        if category.level == 'business':
            children_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)

            return queryset.filter(
                Q(business__categories__category_id=category.category_id) |
                Q(category_id__in=list(children_ids))
            ).distinct()

        # If category is PRODUCT level → direct match
        if category.level == 'product':
            return queryset.filter(category__slug=value).distinct()

        return queryset
    

    def filter_category_slug2(self, queryset, name, value):
        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()

        # 🔹 GLOBAL LEVEL
        if category.level == 'global':
            business_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)
            product_ids = Category.objects.filter(parent__in=business_ids).values_list('category_id', flat=True)

            return queryset.filter(
                Q(business__categories__category_id__in=list(business_ids)) |
                Q(category_id__in=list(product_ids))
            ).distinct()

        # 🔹 BUSINESS LEVEL
        if category.level == 'business':
            product_ids = Category.objects.filter(parent=category).values_list('category_id', flat=True)

            return queryset.filter(
                Q(business__categories__category_id=category.category_id) |
                Q(category_id__in=list(product_ids))
            ).distinct()

        # 🔹 PRODUCT LEVEL
        if category.level == 'product':
            return queryset.filter(category__slug=value).distinct()

        return queryset



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



import django_filters
from django.db.models import (
    Q, F, Min, Max, Count, ExpressionWrapper, FloatField
)
from .models import Product, Business


class ProductFilter_new1(django_filters.FilterSet):

    # 🔍 BASIC SEARCH
    search = django_filters.CharFilter(method='filter_search')

    # 🌐 BUSINESS
    business = django_filters.CharFilter(method='filter_business')

    # 📂 CATEGORY
    category = django_filters.CharFilter(method='filter_category')

    # 🏷 BRAND
    brand = django_filters.CharFilter(method='filter_brand')

    # 🎛 ATTRIBUTE FILTER (color:Black,size:M|material:Leather)
    attributes = django_filters.CharFilter(method='filter_attributes')

    # 💰 PRICE RANGE (0-499,500-999,1000+)
    price = django_filters.CharFilter(method='filter_price_range')

    # 🏷 DISCOUNT RANGE (10-19,20-29,50+)
    discount = django_filters.CharFilter(method='filter_discount_range')

    # ⭐ RATING
    rating = django_filters.CharFilter(method='filter_rating')

    # 📦 INVENTORY
    in_stock = django_filters.BooleanFilter(method='filter_stock')

    # 🔥 SORTING
    ordering = django_filters.OrderingFilter(
        fields=(
            ('min_price', 'price_asc'),
            ('-min_price', 'price_desc'),
            ('-rating', 'rating_desc'),
            ('-created_at', 'latest'),
        )
    )

    class Meta:
        model = Product
        fields = []

    # -----------------------------------------------
    # INIT — Annotate PRICES + DISCOUNTS once
    # -----------------------------------------------
    def __init__(self, data=None, queryset=None, *args, **kwargs):
        if queryset is not None:
            queryset = queryset.annotate(
                min_price=Min('variants__selling_price'),
                max_price=Max('variants__selling_price'),
                discount=ExpressionWrapper(
                    (F('variants__mrp') - F('variants__selling_price')) * 100 / F('variants__mrp'),
                    output_field=FloatField()
                )
            )
        super().__init__(data=data, queryset=queryset, *args, **kwargs)

    # -----------------------------------------------
    # FILTER LOGIC
    # -----------------------------------------------
    def filter_search(self, qs, name, value):
        return qs.filter(
            Q(product_name__icontains=value) |
            Q(brand__icontains=value) |
            Q(model_no__icontains=value)
        )

    def filter_business(self, qs, name, value):
        if value.isdigit():
            return qs.filter(business_id=value)
        return qs.filter(business__slug=value)

    def filter_category(self, qs, name, value):
        return qs.filter(category_id__in=value.split(','))

    def filter_brand(self, qs, name, value):
        return qs.filter(brand__in=value.split(','))

    def filter_attributes(self, qs, name, value):
        for block in value.split('|'):
            key, vals = block.split(':')
            q = Q()
            for v in vals.split(','):
                q |= Q(attributes__contains={key: v})
            qs = qs.filter(q)
        return qs

    def filter_price_range(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            if '-' in r:
                mn, mx = r.split('-')
                q |= Q(min_price__gte=float(mn), min_price__lte=float(mx))
            else:
                q |= Q(min_price__gte=float(r))
        return qs.filter(q)

    def filter_discount_range(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            if '-' in r:
                mn, mx = r.split('-')
                q |= Q(discount__gte=float(mn), discount__lte=float(mx))
            else:
                q |= Q(discount__gte=float(r))
        return qs.filter(q)

    def filter_rating(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            q |= Q(rating__gte=float(r))
        return qs.filter(q)

    def filter_stock(self, qs, name, value):
        return qs.filter(variants__stock__gt=0) if value else qs.filter(variants__stock=0)

    # return distinct
    @property
    def qs(self):
        return super().qs.distinct()

    # -----------------------------------------------
    # FACET OUTPUT for Filters Section
    # -----------------------------------------------
    def get_facets(self, qs):

        # CATEGORY BUCKET
        categories = list(
            qs.values('category_id', 'category__name')
            .annotate(count=Count('product_id'))
        )

        # BRAND BUCKET
        brands = list(
            qs.values('brand').annotate(count=Count('brand'))
        )

        # ATTRIBUTE BUCKET
        attributes = {}
        for p in qs:
            if p.attributes:
                for k, v in p.attributes.items():
                    attributes.setdefault(k, set()).add(v)
        attributes = {k: list(v) for k, v in attributes.items()}

        # PRICE BUCKETS
        PRICE_BUCKETS = [(0,499),(500,999),(1000,4999),(5000,9999),(10000,None)]
        price=[]
        for mn,mx in PRICE_BUCKETS:
            count = qs.filter(min_price__gte=mn, min_price__lte=mx).count() if mx else qs.filter(min_price__gte=mn).count()
            price.append({"label":f"{mn}-{mx}" if mx else f"{mn}+", "min":mn, "max":mx, "count":count})

        # DISCOUNT BUCKETS
        DISCOUNT_BUCKETS = [(0,9),(10,19),(20,29),(30,49),(50,None)]
        discount=[]
        for mn,mx in DISCOUNT_BUCKETS:
            count = qs.filter(discount__gte=mn, discount__lte=mx).count() if mx else qs.filter(discount__gte=mn).count()
            discount.append({"label":f"{mn}-{mx}%" if mx else f"{mn}%+", "min":mn, "max":mx, "count":count})

        # RATING BUCKET
        rating=[
            {"label":"4★ & up","value":4,"count":qs.filter(rating__gte=4).count()},
            {"label":"3★ & up","value":3,"count":qs.filter(rating__gte=3).count()},
            {"label":"2★ & up","value":2,"count":qs.filter(rating__gte=2).count()},
        ]

        # STOCK BUCKET
        inventory=[
            {"label":"In Stock","value":True,"count":qs.filter(variants__stock__gt=0).count()},
            {"label":"Out of Stock","value":False,"count":qs.filter(variants__stock=0).count()},
        ]

        # SORT OPTIONS
        sorting=[
            {"label":"Latest","value":"latest"},
            {"label":"Price Low→High","value":"price_asc"},
            {"label":"Price High→Low","value":"price_desc"},
            {"label":"Rating High→Low","value":"rating_desc"},
        ]

        return {
            "categories": categories,
            "brands": brands,
            "attributes": attributes,
            "price": price,
            "discount": discount,
            "rating": rating,
            "inventory": inventory,
            "sorting": sorting
        }




import django_filters
from django.db.models import Q, F, Min, Max, Count, ExpressionWrapper, FloatField
from .models import Product

class ProductFilter_new2(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')
    business = django_filters.CharFilter(method='filter_business')
    category = django_filters.CharFilter(method='filter_category')
    brand = django_filters.CharFilter(method='filter_brand')
    attributes = django_filters.CharFilter(method='filter_attributes')
    price = django_filters.CharFilter(method='filter_price_range')
    discount = django_filters.CharFilter(method='filter_discount_range')
    rating = django_filters.CharFilter(method='filter_rating')
    in_stock = django_filters.BooleanFilter(method='filter_stock')
    verification_status = django_filters.CharFilter(method='filter_verification_status')

    ordering = django_filters.OrderingFilter(
        fields=(
            ('min_price', 'price_asc'),
            ('-min_price', 'price_desc'),
            ('-rating', 'rating_desc'),
            ('-created_at', 'latest'),
        )
    )

    class Meta:
        model = Product
        fields = []

    def __init__(self, data=None, queryset=None, *args, **kwargs):
        if queryset is not None:
            queryset = queryset.annotate(
                min_price=Min('variants__selling_price'),
                max_price=Max('variants__selling_price'),
                discount=ExpressionWrapper(
                    (F('variants__mrp') - F('variants__selling_price')) * 100 / F('variants__mrp'),
                    output_field=FloatField()
                )
            )
        super().__init__(data=data, queryset=queryset, *args, **kwargs)

    # 🔍 SEARCH
    def filter_search(self, qs, name, value):
        return qs.filter(
            Q(product_name__icontains=value) |
            Q(brand__icontains=value) |
            Q(model_no__icontains=value)
        )

    def filter_business(self, qs, name, value):
        if value.isdigit():
            return qs.filter(business_id=value)
        return qs.filter(business__slug=value)

    def filter_category(self, qs, name, value):
        return qs.filter(category_id__in=value.split(','))

    def filter_brand(self, qs, name, value):
        return qs.filter(brand__in=value.split(','))

    def filter_verification_status(self, qs, name, value):
        return qs.filter(verification_status__in=value.split(','))

    def filter_attributes(self, qs, name, value):
        for block in value.split('|'):
            key, vals = block.split(':')
            q = Q()
            for v in vals.split(','):
                q |= Q(attributes__contains={key: v})
            qs = qs.filter(q)
        return qs

    def filter_price_range(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            if '-' in r:
                mn, mx = r.split('-')
                q |= Q(min_price__gte=float(mn), min_price__lte=float(mx))
            else:
                q |= Q(min_price__gte=float(r))
        return qs.filter(q)

    def filter_discount_range(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            if '-' in r:
                mn, mx = r.split('-')
                q |= Q(discount__gte=float(mn), discount__lte=float(mx))
            else:
                q |= Q(discount__gte=float(r))
        return qs.filter(q)

    def filter_rating(self, qs, name, value):
        q = Q()
        for r in value.split(','):
            q |= Q(rating__gte=float(r))
        return qs.filter(q)

    def filter_stock(self, qs, name, value):
        return qs.filter(variants__stock__gt=0) if value else qs.filter(variants__stock=0)

    @property
    def qs(self):
        return super().qs.distinct()

    # --------------------------------------------------
    # FACET GENERATOR (For UI filters)
    # --------------------------------------------------
    def get_facets(self, qs):

        categories = list(
            qs.values('category_id', 'category__name')
            .annotate(count=Count('product_id'))
        )

        brands = list(
            qs.values('brand').annotate(count=Count('brand'))
        )

        attributes = {}
        for p in qs:
            if p.attributes:
                for k, v in p.attributes.items():
                    attributes.setdefault(k, set()).add(v)
        attributes = {k: list(v) for k, v in attributes.items()}

        PRICE_BUCKETS = [(0,499),(500,999),(1000,4999),(5000,9999),(10000,None)]
        price=[]
        for mn,mx in PRICE_BUCKETS:
            count = qs.filter(min_price__gte=mn, min_price__lte=mx).count() if mx else qs.filter(min_price__gte=mn).count()
            price.append({"label":f"{mn}-{mx}" if mx else f"{mn}+", "min":mn, "max":mx, "count":count})

        DISCOUNT_BUCKETS = [(0,9),(10,19),(20,29),(30,49),(50,None)]
        discount=[]
        for mn,mx in DISCOUNT_BUCKETS:
            count = qs.filter(discount__gte=mn, discount__lte=mx).count() if mx else qs.filter(discount__gte=mn).count()
            discount.append({"label":f"{mn}-{mx}%" if mx else f"{mn}%+", "min":mn, "max":mx, "count":count})

        rating = [
            {"label":"4★ & up","value":4,"count":qs.filter(rating__gte=4).count()},
            {"label":"3★ & up","value":3,"count":qs.filter(rating__gte=3).count()},
            {"label":"2★ & up","value":2,"count":qs.filter(rating__gte=2).count()},
        ]

        inventory=[
            {"label":"In Stock","value":True,"count":qs.filter(variants__stock__gt=0).count()},
            {"label":"Out of Stock","value":False,"count":qs.filter(variants__stock=0).count()},
        ]

        sorting=[
            {"label":"Latest","value":"latest"},
            {"label":"Price Low→High","value":"price_asc"},
            {"label":"Price High→Low","value":"price_desc"},
            {"label":"Rating High→Low","value":"rating_desc"},
        ]

        return {
            "categories": categories,
            "brands": brands,
            "attributes": attributes,
            "price": price,
            "discount": discount,
            "rating": rating,
            "inventory": inventory,
            "sorting": sorting,
        }


