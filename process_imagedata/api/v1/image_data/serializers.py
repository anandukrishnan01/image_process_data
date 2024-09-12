from rest_framework import serializers
from image_data.models import ImageProcessingRequest, Product


class ImageProcessingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProcessingRequest
        fields = ['request_id', 'status', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # fields = ['serial_number', 'product_name', 'input_image_urls', 'output_image_urls']
        fields = '__all__'
