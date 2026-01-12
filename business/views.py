from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from property.models import  *
import random
from django.core.mail import send_mail
from django.utils.cache import caches
from mlm.settings import *
from PIL import Image
from django.db.models import Count, Q, Sum
import random
import requests
from urllib.parse import quote  # ✅ for URL encoding
from django.core.cache import cache
from django.conf import settings
from mlm.pagination import GlobalPagination

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Business, Product, ProductVariant, ProductMedia
from .serializers import BusinessSerializer, ProductSerializer

from .filters import BusinessFilter, ProductFilter




class CategoryListCreateView(APIView):

    # def get(self, request):
    #     try:
    #         categories = Category.objects.filter(is_active=True)

    #         level = request.GET.get('level')
    #         parent = request.GET.get('parent')

    #         if level:
    #             categories = categories.filter(level=level)

    #         if parent:
    #             categories = categories.filter(parent_id=parent)
    #         else:
    #             categories = categories.filter(parent__isnull=True)

    #         # ✅ Manual pagination
    #         paginator = GlobalPagination()
    #         paginated_qs = paginator.paginate_queryset(categories, request)

    #         serializer = CategorySerializer(paginated_qs, many=True)
    #         return paginator.get_paginated_response(serializer.data)

    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

    def get(self, request):
        try:
            queryset = Category.objects.all().order_by('-category_id')

            # ---------------- FILTERS ----------------
            search = request.GET.get('search')
            level = request.GET.get('level')
            parent = request.GET.get('parent')
            slug = request.GET.get('slug')
            is_active = request.GET.get('is_active')

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(slug__icontains=search)
                )

            if level:
                queryset = queryset.filter(level__iexact=level)

            if parent:
                queryset = queryset.filter(parent_id=parent)

            if slug:
                queryset = queryset.filter(slug=slug)

            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')

            # ---------------- PAGINATION ----------------
            paginator = GlobalPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = CategorySerializer(page, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Category created successfully", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CategoryDetailView(APIView):

    def get(self, request, category_id):
        try:
            category = get_object_or_404(Category, category_id=category_id)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, category_id):
        try:
            category = get_object_or_404(Category, category_id=category_id)
            serializer = CategorySerializer(
                category,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, category_id):
        try:
            category = get_object_or_404(Category, category_id=category_id)
            category.delete()
            return Response(
                {"message": "Category deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryBulkCreateView(APIView):
    def post(self, request):
        serializer = CategorySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Categories created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








# Business List & Create


class BusinessListCreateView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = Business.objects.all().order_by('-created_at')

            # ✅ django-filters applied
            queryset = BusinessFilter(
                request.GET,
                queryset=queryset
            ).qs

            paginator = GlobalPagination()
            paginated_qs = paginator.paginate_queryset(queryset, request)

            serializer = BusinessSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = BusinessSerializer(data=request.data)
            if serializer.is_valid():
                # serializer.save(user=request.user)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Business Detail (GET, PUT, DELETE)


class BusinessDetailView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        try:
            business = get_object_or_404(Business, business_id=business_id)
            serializer = BusinessSerializer(business)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, business_id):
        try:
            business = get_object_or_404(Business, business_id=business_id)
            serializer = BusinessSerializer(
                business,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, business_id):
        try:
            get_object_or_404(Business, business_id=business_id).delete()
            return Response(
                {"message": "Business deleted"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class BusinessByUserIDView(APIView):
    """
    GET → List businesses by user ID (paginated)
    """

    def get(self, request, id):
        try:
            businesses = (
                Business.objects
                .filter(user_id=id)
                .order_by('-created_at')
            )

            paginator = GlobalPagination()
            paginated_businesses = paginator.paginate_queryset(
                businesses,
                request
            )

            serializer = BusinessSerializer(
                paginated_businesses,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Offer List & Create

class OfferListCreateView(APIView):

    def get(self, request):
        try:
            offers = Offer.objects.all().order_by('-id')

            paginator = GlobalPagination()
            paginated_offers = paginator.paginate_queryset(
                offers,
                request
            )

            serializer = OfferSerializer(
                paginated_offers,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = OfferSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Offer Retrieve, Update, Delete
class OfferDetailView(APIView):
    def get(self, request, id):
        try:
            offer = get_object_or_404(Offer, id=id)
            serializer = OfferSerializer(offer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            offer = get_object_or_404(Offer, id=id)
            serializer = OfferSerializer(offer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            offer = get_object_or_404(Offer, id=id)
            offer.delete()
            return Response({'message': 'Offer deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class OfferByUserView(APIView):
    """
    GET → List offers by user ID (paginated)
    """

    def get(self, request, user_id):
        try:
            offers = (
                Offer.objects
                .filter(user_id=user_id)
                .order_by('-id')
            )

            paginator = GlobalPagination()
            paginated_offers = paginator.paginate_queryset(
                offers,
                request
            )

            serializer = OfferSerializer(
                paginated_offers,
                many=True
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------------
# Product List & Create API
# -------------------------------

class ProductListCreateView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = Product.objects.select_related(
                'business', 'category'
            ).prefetch_related(
                'variants', 'media'
            ).order_by('-created_at')

            # ✅ django-filters (Product + Variant level)
            queryset = ProductFilter(
                request.GET,
                queryset=queryset
            ).qs

            paginator = GlobalPagination()
            paginated_qs = paginator.paginate_queryset(queryset, request)

            serializer = ProductSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def get(self, request):

    #     business_param = request.GET.get('business')

    #     # base_qs = Product.objects.filter(is_active=True, verification_status='verified')
    #     base_qs = Product.objects.filter()

    #     business_data = None
    #     if business_param:
    #         business = Business.objects.filter(slug=business_param).first()
    #         if business:
    #             base_qs = base_qs.filter(business=business)
    #             business_data = {
    #                 "id": business.business_id,
    #                 "name": business.business_name,
    #                 "slug": business.slug,
    #                 "city": business.city,
    #                 "state": business.state,
    #                 "rating": float(business.rating),
    #                 "status": "Open"
    #             }

    #     f = ProductFilter(request.GET, queryset=base_qs)
    #     filtered_qs = f.qs

    #     filters = f.get_facets(filtered_qs)

    #     paginator = GlobalPagination()
    #     page = paginator.paginate_queryset(filtered_qs, request)

    #     products = []
    #     for p in page:
    #         products.append({
    #             "product_id": p.product_id,
    #             "product_name": p.product_name,
    #             "brand": p.brand,
    #             "min_price": float(p.min_price) if p.min_price else None,
    #             "max_price": float(p.max_price) if p.max_price else None,
    #             "discount": float(p.discount) if p.discount else None,
    #             "rating": float(p.rating),
    #             "category": p.category_id,
    #             "attributes": p.attributes or {},
    #             "business": p.business_id,
    #             "media": [
    #                 {
    #                     "file": m.file.url,
    #                     "media_type": m.media_type,
    #                     "is_primary": m.is_primary
    #                 }
    #                 # for m in p.media.filter(is_primary=True)[:1]
    #                 for m in p.media.filter()
    #             ]
    #         })

    #     return Response({
    #         "business": business_data,
    #         "filters": filters,
    #         "products": products,
    #         "pagination": {
    #             "page": paginator.page.number,
    #             "page_size": paginator.page.paginator.per_page,
    #             "total": paginator.page.paginator.count,
    #             "total_pages": paginator.page.paginator.num_pages,
    #         }
    #     })

    @transaction.atomic
    def post(self, request):
        """
        Nested Create:
        Product + Variants + Media
        """
        try:
            product_data = request.data.get('product')
            variants = request.data.get('variants', [])
            media_files = request.FILES.getlist('media')

            if not product_data:
                return Response(
                    {"error": "Product data is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            business = get_object_or_404(
                Business,
                business_id=product_data.get('business')
            )

            # ✅ Create Product
            product = Product.objects.create(
                business=business,
                product_name=product_data.get('product_name'),
                description=product_data.get('description'),
                brand=product_data.get('brand'),
                category_id=product_data.get('category'),
                attributes=product_data.get('attributes'),
                verification_status='pending'
            )

            # ✅ Create Variants
            for v in variants:
                ProductVariant.objects.create(
                    product=product,
                    **v
                )

            # ✅ Create Media
            for index, file in enumerate(media_files):
                ProductMedia.objects.create(
                    product=product,
                    media_type='image',
                    file=file,
                    is_primary=index == 0,
                    sort_order=index
                )

            return Response(
                {"message": "Product created", "product_id": product.product_id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------------
# Product Detail (GET, PUT, DELETE)
# -------------------------------

class ProductDetailView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:
            product = get_object_or_404(
                Product.objects.prefetch_related('variants', 'media'),
                product_id=product_id
            )
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @transaction.atomic
    # def put(self, request, product_id):
    #     """
    #     Nested Update:
    #     Product + Replace Variants + Add Media
    #     """
    #     try:
    #         product = get_object_or_404(Product, product_id=product_id)

    #         product_data = request.data.get('product', {})
    #         variants = request.data.get('variants', [])
    #         media_files = request.FILES.getlist('media')

    #         # 🔄 Update product fields
    #         for field, value in product_data.items():
    #             setattr(product, field, value)

    #         product.verification_status = 'pending'
    #         product.save()

    #         # 🔄 Replace variants
    #         ProductVariant.objects.filter(product=product).delete()
    #         for v in variants:
    #             ProductVariant.objects.create(product=product, **v)

    #         # ➕ Add media
    #         for file in media_files:
    #             ProductMedia.objects.create(
    #                 product=product,
    #                 media_type='image',
    #                 file=file
    #             )

    #         return Response(
    #             {"message": "Product updated"},
    #             status=status.HTTP_200_OK
    #         )

    #     except Exception as e:
    #         transaction.set_rollback(True)
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def put(self, request, product_id):
        try:
            product = get_object_or_404(Product, product_id=product_id)

            product_data = request.data.get('product')
            variants = request.data.get('variants')
            media_files = request.FILES.getlist('media')

            # 🔄 Update PRODUCT only if provided
            if product_data:
                for field, value in product_data.items():
                    setattr(product, field, value)

                product.verification_status = 'pending'
                product.save()

            # 🔄 Update VARIANTS only if explicitly sent
            if variants is not None:
                ProductVariant.objects.filter(product=product).delete()

                for v in variants:
                    ProductVariant.objects.create(product=product, **v)

            # ➕ Add MEDIA only if files are sent
            if media_files:
                for file in media_files:
                    ProductMedia.objects.create(
                        product=product,
                        media_type='image',
                        file=file
                    )

            return Response(
                {"message": "Product updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            transaction.set_rollback(True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def delete(self, request, product_id):
        try:
            get_object_or_404(Product, product_id=product_id).delete()
            return Response(
                {"message": "Product deleted"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ------------------------------------
# Get Products by Business ID
# ------------------------------------
class ProductByBusinessView(APIView):
    """
    GET → Get all products for a given business_id
    """
    def get(self, request, business_id):
        try:
            business = get_object_or_404(Business, business_id=business_id)
            products = Product.objects.filter(business_id=business).order_by('-created_at')

            if not products.exists():
                return Response(
                    {"message": "No products found for this business."},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


























class CartListCreateView(APIView):

    # 🔹 GET ALL CART ITEMS (ADMIN / INTERNAL)
    def get(self, request):
        try:
            carts = Cart.objects.select_related(
                'user', 'product', 'property_item'
            ).all()

            serializer = CartSerializer(carts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔹 ADD TO CART
    def post(self, request):
        try:
            user_id = request.data.get("user")
            product_id = request.data.get("product")
            property_id = request.data.get("property_item")
            quantity = int(request.data.get("quantity", 1))

            if not user_id:
                return Response({"error": "user is required"}, status=400)

            # PRODUCT CART
            if product_id:
                product = get_object_or_404(Product, id=product_id)

                if quantity < 1:
                    return Response({"error": "Quantity must be at least 1"}, status=400)

                if product.available_qty < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)

                cart_item, created = Cart.objects.get_or_create(
                    user_id=user_id,
                    product=product,
                    defaults={"quantity": quantity}
                )

                if not created:
                    new_qty = cart_item.quantity + quantity
                    if product.available_qty < new_qty:
                        return Response({"error": "Insufficient stock"}, status=400)

                    cart_item.quantity = new_qty
                    cart_item.save()

            # PROPERTY CART
            elif property_id:
                property_item = get_object_or_404(Property, id=property_id)

                if Cart.objects.filter(user_id=user_id, property_item=property_item).exists():
                    return Response(
                        {"error": "Property already added to cart"},
                        status=400
                    )

                Cart.objects.create(
                    user_id=user_id,
                    property_item=property_item,
                    quantity=1
                )

            else:
                return Response(
                    {"error": "Either product or property_item is required"},
                    status=400
                )

            return Response(
                {"message": "Item added to cart successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartByUserAPIView(APIView):

    

    def get(self, request, user_id):
        try:
            cart_items = Cart.objects.filter(
                user_id=user_id
            ).select_related('product', 'property_item')

            serializer = CartSerializer(cart_items, many=True)

            total_amount = sum(item.subtotal for item in cart_items)

            return Response({
                "items": serializer.data,
                "total_amount": total_amount
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CartDetailView(APIView):
    def get(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)

            quantity = int(request.data.get("quantity", cart_item.quantity))

            if cart_item.product:
                if quantity < 1:
                    return Response({"error": "Quantity must be at least 1"}, status=400)

                if cart_item.product.available_qty < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)

                cart_item.quantity = quantity
                cart_item.save()

            return Response(
                {"message": "Cart updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, id):
        try:
            cart_item = get_object_or_404(Cart, id=id)
            cart_item.delete()
            return Response(
                {"message": "Cart item removed"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)









