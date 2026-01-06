from rest_framework import serializers
from .models import *


# Category Serializer
class PropertyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCategory
        fields = ['property_category_id', 'name']


# Type Serializer
class PropertyTypeSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=PropertyCategory.objects.all())

    class Meta:
        model = PropertyType
        fields = ['property_type_id', 'name', 'category']


# Image Serializer
class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image']


# Video Serializer
class PropertyVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVideo
        fields = ['id', 'video']

# File Serializer
class PropertyFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyFile
        fields = ['id', 'file']


# Amenity Serializer
class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['amenity_id', 'name']




class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    videos = PropertyVideoSerializer(many=True, read_only=True)
    files = PropertyFileSerializer(many=True, read_only=True)

    amenities = serializers.PrimaryKeyRelatedField(queryset=Amenity.objects.all(), many=True)

    class Meta:
        model = Property
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        images = request.FILES.getlist('images')
        videos = request.FILES.getlist('videos')
        files = request.FILES.getlist('files')


        amenities = validated_data.pop('amenities', [])
        property_instance = Property.objects.create(**validated_data)
        property_instance.amenities.set(amenities)

        for image in images:
            PropertyImage.objects.create(property=property_instance, image=image)

        for video in videos:
            PropertyVideo.objects.create(property=property_instance, video=video)

        for file in files:
            PropertyFile.objects.create(property=property_instance, file=file)

        return property_instance
    
    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Handle amenities
        amenities = validated_data.pop('amenities', [])
        instance.amenities.set(amenities)

        # Update other simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Determine the source of data: multipart vs JSON
        is_multipart = request and request.content_type.startswith('multipart')

        # ----------- IMAGE HANDLING -----------
        if is_multipart:
            image_ids = request._request.POST.getlist('image_ids')
            image_files = request._request.FILES.getlist('images')
        else:
            image_ids = request.data.get('image_ids', [])
            image_files = request.FILES.getlist('images') if hasattr(request, 'FILES') else []

        image_id_file_map = dict(zip(image_ids, image_files))

        for img_id, file in image_id_file_map.items():
            try:
                img_obj = PropertyImage.objects.get(id=img_id, property=instance)
                img_obj.image = file
                img_obj.save()
            except PropertyImage.DoesNotExist:
                PropertyImage.objects.create(property=instance, image=file)

        # ----------- VIDEO HANDLING -----------
        if is_multipart:
            video_ids = request._request.POST.getlist('video_ids')
            video_files = request._request.FILES.getlist('videos')
        else:
            video_ids = request.data.get('video_ids', [])
            video_files = request.FILES.getlist('videos') if hasattr(request, 'FILES') else []

        video_id_file_map = dict(zip(video_ids, video_files))

        for vid_id, file in video_id_file_map.items():
            try:
                vid_obj = PropertyVideo.objects.get(id=vid_id, property=instance)
                vid_obj.video = file
                vid_obj.save()
            except PropertyVideo.DoesNotExist:
                PropertyVideo.objects.create(property=instance, video=file)
        
        # -------------------- FILE HANDLING (NEW) --------------------
        if is_multipart:
            file_ids = request._request.POST.getlist('file_ids')
            file_files = request._request.FILES.getlist('files')
        else:
            file_ids = request.data.get('file_ids', [])
            file_files = request.FILES.getlist('files') if hasattr(request, 'FILES') else []

        file_id_file_map = dict(zip(file_ids, file_files))

        for f_id, file in file_id_file_map.items():
            try:
                f_obj = PropertyFile.objects.get(id=f_id, property=instance)
                f_obj.file = file
                f_obj.save()
            except PropertyFile.DoesNotExist:
                PropertyFile.objects.create(property=instance, file=file)

        return instance





class EMIOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMIOption
        fields = ['id', 'property', 'period_months', 'emi_amount']
        read_only_fields = ['emi_amount']




class UserEMISerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEMI
        fields = ['id', 'user', 'property', 'emi_option', 'start_date', 'end_date']
        read_only_fields = ['end_date']



class BookingAmountSlabSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAmountSlab
        fields = ['id', 'min_value', 'max_value', 'booking_amount']






# from transactions.models import *
# class TransactionPropertySerializer(serializers.ModelSerializer):
#     property_id = PropertySerializer()

#     class Meta:
#         model = Transaction
#         fields = [
#             'transaction_id',  'paid_amount', 'property_value',
#             'payment_type', 'transaction_date','property_id'
#         ]





class PropertyFullSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    property_type = serializers.CharField(source='property_type.name', read_only=True)
    amenities = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = Property
        fields = '__all__'








