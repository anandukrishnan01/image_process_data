from django.contrib import admin
from image_data.models import Product, ImageProcessingRequest
# Register your models here.

admin.site.register(Product)
admin.site.register(ImageProcessingRequest)