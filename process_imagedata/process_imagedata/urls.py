from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include

from process_imagedata import settings

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/v1/image_data/', include('api.v1.image_data.urls', namespace="api_v1_image_data")),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
