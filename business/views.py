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
from .filters import *

import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView




class CategoryListCreateView_old(APIView):

    

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


class CategoryListCreateView(APIView):

    def get(self, request):
        try:
            queryset = Category.objects.all().order_by('-category_id')

            # Apply filters
            category_filter = CategoryFilter(request.GET, queryset=queryset)
            queryset = category_filter.qs

            # Pagination
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

    # def get(self, request):
    #     try:
    #         queryset = Product.objects.select_related(
    #             'business', 'category'
    #         ).prefetch_related(
    #             'variants__media'
    #         ).order_by('-created_at')
    #         # ✅ django-filters (Product + Variant level)
    #         queryset = ProductFilter(
    #             request.GET,
    #             queryset=queryset
    #         ).qs

    #         paginator = GlobalPagination()
    #         paginated_qs = paginator.paginate_queryset(queryset, request)
    #         serializer = ProductSerializer(paginated_qs, many=True)
    #         return paginator.get_paginated_response(serializer.data)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=500)

    def get(self, request):
        queryset = Product.objects.select_related(
            'business', 'category'
        ).prefetch_related(
            'variants__media'
        ).order_by('-created_at')

        queryset = ProductFilter(request.GET, queryset=queryset).qs

        variant_id = request.GET.get('variant_id')

        if variant_id:
            queryset = queryset.filter(variants__id=variant_id).distinct()

            for product in queryset:
                product._filtered_variants = product.variants.filter(id=variant_id)

        paginator = GlobalPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)

        # inject filtered variants into serializer output
        data = ProductSerializer(paginated_qs, many=True).data

        if variant_id:
            for item, product in zip(data, paginated_qs):
                item["variants"] = ProductVariantSerializer(product._filtered_variants, many=True).data

        return paginator.get_paginated_response(data)


    @transaction.atomic
    def post(self, request):
        try:
            product_data = request.data.get('product')
            variants_data = request.data.get('variants', [])

            # parse JSON if coming as string (from Postman)
            if isinstance(product_data, str):
                product_data = json.loads(product_data)
            if isinstance(variants_data, str):
                variants_data = json.loads(variants_data)

            if not product_data:
                return Response({"error": "Product data is required"}, status=400)

            business = get_object_or_404(Business, business_id=product_data.get('business'))

            product = Product.objects.create(
                business=business,
                product_name=product_data.get('product_name'),
                description=product_data.get('description'),
                brand=product_data.get('brand'),
                category_id=product_data.get('category'),
                attributes=product_data.get('attributes'),
                verification_status='pending'
            )

            # create variants + media
            for v in variants_data:
                variant = ProductVariant.objects.create(
                    product=product,
                    **{k: v[k] for k in v if k not in ('id', 'media')}
                )

                media_list = v.get('media', [])
                for m in media_list:
                    uploaded = request.FILES.get('media_file')
                    if uploaded:
                        ProductMedia.objects.create(
                            product=product,
                            variant=variant,
                            media_type=m.get('media_type', 'image'),
                            file=uploaded
                        )

            return Response({"message": "Product created", "product_id": product.product_id}, status=201)

        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=500)



# -------------------------------
# Product Detail (GET, PUT, DELETE)
# -------------------------------

class ProductDetailView(APIView):

    # def get(self, request, product_id):
    #     try:
    #         product = get_object_or_404(
    #             Product.objects.prefetch_related('variants__media'),
    #             product_id=product_id
    #         )
    #         serializer = ProductSerializer(product)
    #         return Response(serializer.data, status=200)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=500)
    def get(self, request, product_id):
        product = get_object_or_404(
            Product.objects.prefetch_related('variants__media'),
            product_id=product_id
        )

        variant_id = request.GET.get('variant_id')

        if variant_id:
            if not product.variants.filter(id=variant_id).exists():
                return Response({"error": "Variant not found for this product"}, status=404)

            product._filtered_variants = product.variants.filter(id=variant_id)
            data = ProductSerializer(product).data
            data["variants"] = ProductVariantSerializer(product._filtered_variants, many=True).data
            return Response(data, status=200)

        return Response(ProductSerializer(product).data, status=200)

   


    @transaction.atomic
    def put(self, request, product_id):
        try:
            product = get_object_or_404(Product, product_id=product_id)

            product_data = request.data.get('product')
            variants_data = request.data.get('variants', [])

            # parse JSON if sent as text
            if isinstance(product_data, str):
                product_data = json.loads(product_data)
            if isinstance(variants_data, str):
                variants_data = json.loads(variants_data)

            # update product
            if product_data:
                for field, value in product_data.items():
                    setattr(product, field, value)
                product.save()

            # update variants + media
            for v in variants_data:
                variant_id = v.get('id')
                media_list = v.get('media', [])

                variant = ProductVariant.objects.filter(id=variant_id, product=product).first()
                if not variant:
                    continue

                for field, value in v.items():
                    if field not in ('id', 'media'):
                        setattr(variant, field, value)
                variant.save()

                # update media inside variant
                for m in media_list:
                    media_id = m.get('id')
                    uploaded = request.FILES.get('media_file')

                    if media_id:
                        media_obj = ProductMedia.objects.filter(
                            id=media_id, variant=variant, product=product
                        ).first()

                        if media_obj:
                            for field, value in m.items():
                                if field not in ('id', 'file'):
                                    setattr(media_obj, field, value)
                            if uploaded:
                                media_obj.file = uploaded
                            media_obj.save()

                    else:
                        # new media append
                        if uploaded:
                            ProductMedia.objects.create(
                                product=product,
                                variant=variant,
                                media_type=m.get('media_type', 'image'),
                                file=uploaded,
                                sort_order=m.get('sort_order', 0)
                            )

            return Response({"message": "Product updated successfully"}, status=200)

        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=500)

    def delete(self, request, product_id):
        try:
            variant_param = request.query_params.get('variants')
            media_param = request.query_params.get('media')

            if media_param:
                ids = [int(i) for i in media_param.split(',') if i.isdigit()]
                deleted, _ = ProductMedia.objects.filter(
                    product_id=product_id, id__in=ids
                ).delete()
                return Response({"message": f"{deleted} media deleted"}, status=200)

            if variant_param:
                ids = [int(i) for i in variant_param.split(',') if i.isdigit()]
                deleted, _ = ProductVariant.objects.filter(
                    product_id=product_id, id__in=ids
                ).delete()
                return Response({"message": f"{deleted} variants deleted"}, status=200)

            # delete full product
            get_object_or_404(Product, product_id=product_id).delete()
            return Response({"message": "Product deleted"}, status=204)

        except Exception as e:
            return Response({"error": str(e)}, status=500)



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









