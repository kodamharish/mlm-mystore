import django_filters
from django.db.models import Q, Min, Max
from .models import Business, Product, ProductVariant
from .models import *
from django.db.models import F, ExpressionWrapper, DecimalField


import django_filters
from django.db.models import Q
from .models import Category

class CategoryFilter_old(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')
    level = django_filters.CharFilter(field_name='level', lookup_expr='iexact')
    parent = django_filters.NumberFilter(field_name='parent_id')
    slug = django_filters.CharFilter(field_name='slug')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    user_id = django_filters.NumberFilter(method='filter_user_categories')

    class Meta:
        model = Category
        fields = []

    # OLD: search
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value)
        )

    # NEW: category filtering by user
    def filter_user_categories(self, queryset, name, value):
        level = self.data.get('level', None)

        # User → Business → Business Categories (level=business)
        business_categories = Category.objects.filter(
            businesses__user_id=value,
            level='business'
        ).distinct()

        # User → Business → Product Categories (children)
        product_categories = Category.objects.filter(
            parent__in=business_categories,
            level='product'
        ).distinct()

        if level == 'business':
            return business_categories
        elif level == 'product':
            return product_categories

        # if no level → return both
        return (business_categories | product_categories).distinct()



class CategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    level = django_filters.CharFilter(field_name='level', lookup_expr='iexact')
    parent = django_filters.NumberFilter(field_name='parent_id')
    slug = django_filters.CharFilter(field_name='slug')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    user_id = django_filters.NumberFilter(method='filter_user_business_tree')
    business_id = django_filters.NumberFilter(method='filter_dummy')   # <-- key fix

    class Meta:
        model = Category
        fields = []

    #
    # prevent django-filter from auto-applying category.business_id
    #
    def filter_dummy(self, queryset, name, value):
        return queryset   # do nothing here!

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(slug__icontains=value)
        )

    def filter_user_business_tree(self, queryset, name, user_id):
        level = self.data.get('level')
        business_id = self.data.get('business_id')

        # validate business belongs to user
        if business_id:
            if not Business.objects.filter(business_id=business_id, user_id=user_id).exists():
                return queryset.none()

        # 1. get business-level categories allowed for the user
        business_categories = Category.objects.filter(
            level='business',
            businesses__user_id=user_id
        ).distinct()

        if business_id:
            business_categories = business_categories.filter(
                businesses__business_id=business_id
            ).distinct()

        if level == 'business':
            return business_categories

        # 2. get product-level categories under those business categories
        product_categories = Category.objects.filter(
            level='product',
            parent__in=business_categories
        ).distinct()

        if level == 'product':
            return product_categories

        return (business_categories | product_categories).distinct()




class BusinessFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')

    # Seller
    user_id = django_filters.NumberFilter(field_name='user_id')

    business_type = django_filters.CharFilter(field_name='business_type')
    verification_status = django_filters.CharFilter(field_name='verification_status')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    #category = django_filters.NumberFilter(field_name='categories__id')

    # Filter by category_id
    #category = django_filters.NumberFilter(field_name='categories__id')
    category = django_filters.NumberFilter(field_name='categories')


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




class ProductFilter_old(django_filters.FilterSet):

    search = django_filters.CharFilter(method='filter_search')

    business = django_filters.NumberFilter(field_name='business_id')
    business_slug = django_filters.CharFilter(field_name='business__slug', lookup_expr='iexact')

    # Filter by product category slug
    #category_slug = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    #category_slug = django_filters.CharFilter(method='filter_category_slug')


    category_slug = django_filters.CharFilter(method='filter_category_slug')
    category_id = django_filters.NumberFilter(method='filter_category_id')
    variant_id = django_filters.NumberFilter(method='filter_variant_id')
    user_id = django_filters.NumberFilter(method='filter_user_products')
    
    def filter_user_products(self, queryset, name, value):
        qs = queryset.filter(business__user_id=value).distinct()
        return qs if qs.exists() else queryset.none()



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
    discount_range = django_filters.CharFilter(method='filter_discount_range')
    price_range = django_filters.CharFilter(method='filter_price_range')



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
    def filter_variant_id(self, queryset, name, value):
        qs = queryset.filter(variants__id=value).distinct()

        # If no matching product for variant → return zero results
        if not qs.exists():
            return queryset.none()

        return qs

    from django.db.models import F, ExpressionWrapper, DecimalField

    def filter_discount_range_old(self, queryset, name, value):
        ranges = {
            "0-9": (0, 9),
            "10-19": (10, 19),
            "20-29": (20, 29),
            "30-39": (30, 39),
            "40-49": (40, 49),
            "50-59": (50, 59),
            "60+": (60, None),
        }

        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        qs = queryset.annotate(
            discount=ExpressionWrapper(
                ((F('variants__mrp') - F('variants__selling_price')) / F('variants__mrp')) * 100,
                output_field=DecimalField(max_digits=5, decimal_places=2)
            )
        )

        if high is None:
            qs = qs.filter(discount__gte=low)
        else:
            qs = qs.filter(discount__gte=low, discount__lte=high)

        return qs.distinct() if qs.exists() else queryset.none()
        
    def filter_price_range_old(self, queryset, name, value):
        ranges = {
            "0-499": (0, 499),
            "500-999": (500, 999),
            "1000-4999": (1000, 4999),
            "5000-9999": (5000, 9999),
            "10000+": (10000, None),
        }

        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        if high is None:
            qs = queryset.filter(variants__selling_price__gte=low)
        else:
            qs = queryset.filter(
                variants__selling_price__gte=low,
                variants__selling_price__lte=high
            )

        return qs.distinct() if qs.exists() else queryset.none()
     

    



    

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

    def filter_price_range(self, queryset, name, value):

        ranges = {
            "0-499": (0, 499),
            "500-999": (500, 999),
            "1000-4999": (1000, 4999),
            "5000-9999": (5000, 9999),
            "10000+": (10000, None),
        }

        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        variant_qs = ProductVariant.objects.all()

        if high is None:
            variant_qs = variant_qs.filter(selling_price__gte=low)
        else:
            variant_qs = variant_qs.filter(selling_price__gte=low, selling_price__lte=high)

        return queryset.filter(variants__in=variant_qs).distinct()

    def filter_discount_range(self, queryset, name, value):

        ranges = {
            "0-9": (0, 9),
            "10-19": (10, 19),
            "20-29": (20, 29),
            "30-39": (30, 39),
            "40-49": (40, 49),
            "50-59": (50, 59),
            "60+": (60, None),
        }

        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        variant_qs = ProductVariant.objects.annotate(
            discount=ExpressionWrapper(
                ((F('mrp') - F('selling_price')) / F('mrp')) * 100,
                output_field=DecimalField(max_digits=5, decimal_places=2)
            )
        )

        if high is None:
            variant_qs = variant_qs.filter(discount__gte=low)
        else:
            variant_qs = variant_qs.filter(discount__gte=low, discount__lte=high)

        return queryset.filter(variants__in=variant_qs).distinct()

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
    variant_id = django_filters.NumberFilter(method='filter_variant_id')
    user_id = django_filters.NumberFilter(method='filter_user_products')
    exclude_user_id = django_filters.NumberFilter(method='filter_exclude_user_products')
    #exclude_user_id = django_filters.NumberFilter(method='filter_exclude_user')


    
    def filter_user_products(self, queryset, name, value):
        qs = queryset.filter(business__user_id=value).distinct()
        return qs if qs.exists() else queryset.none()

    
    def filter_exclude_user_products(self, queryset, name, value):
        qs = queryset.exclude(business__user_id=value).distinct()
        return qs if qs.exists() else queryset.none()

    # def filter_exclude_user(self, queryset, name, value):
    #     return queryset.exclude(business__user_id=value).distinct()





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
    discount_range = django_filters.CharFilter(method='filter_discount_range')
    price_range = django_filters.CharFilter(method='filter_price_range')



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
    def filter_variant_id(self, queryset, name, value):
        qs = queryset.filter(variants__id=value).distinct()

        # If no matching product for variant → return zero results
        if not qs.exists():
            return queryset.none()

        return qs

    from django.db.models import F, ExpressionWrapper, DecimalField

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

    def filter_price_range(self, queryset, name, value):

        # ranges = {
        #     "0-499": (0, 499),
        #     "500-999": (500, 999),
        #     "1000-4999": (1000, 4999),
        #     "5000-9999": (5000, 9999),
        #     "10000+": (10000, None),
        # }

        ranges = {
        "0-500": (0, 500), # 0 ≤ price < 500
        "500-1000": (500, 1000), # 500 ≤ price < 1000
        "1000-5000": (1000, 5000),
        "5000-10000": (5000, 10000),
        "10000+": (10000, None),
        }


        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        variant_qs = ProductVariant.objects.all()

        if high is None:
            variant_qs = variant_qs.filter(selling_price__gte=low)
        else:
            variant_qs = variant_qs.filter(selling_price__gte=low, selling_price__lte=high)

        return queryset.filter(variants__in=variant_qs).distinct()

    def filter_discount_range(self, queryset, name, value):

        # ranges = {
        #     "0-9": (0, 9),
        #     "10-19": (10, 19),
        #     "20-29": (20, 29),
        #     "30-39": (30, 39),
        #     "40-49": (40, 49),
        #     "50-59": (50, 59),
        #     "60+": (60, None),
        # }

        ranges = {
        "0-10": (0, 10),
        "10-20": (10, 20),
        "20-30": (20, 30),
        "30-40": (30, 40),
        "40-50": (40, 50),
        "50-60": (50, 60),
        "60+": (60, None),
        }


        if value not in ranges:
            return queryset.none()

        low, high = ranges[value]

        variant_qs = ProductVariant.objects.annotate(
            discount=ExpressionWrapper(
                ((F('mrp') - F('selling_price')) / F('mrp')) * 100,
                output_field=DecimalField(max_digits=5, decimal_places=2)
            )
        )

        if high is None:
            variant_qs = variant_qs.filter(discount__gte=low)
        else:
            variant_qs = variant_qs.filter(discount__gte=low, discount__lte=high)

        return queryset.filter(variants__in=variant_qs).distinct()

    @property
    def qs(self):
        return super().qs.annotate(
            min_price=Min('variants__selling_price'),
            max_price=Max('variants__selling_price')
        )



