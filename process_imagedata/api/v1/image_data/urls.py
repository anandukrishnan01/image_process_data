from django.urls import path
from .views import UploadCSV, StatusAPIView, ExportCSV

app_name = "image_data"


urlpatterns = [
    path('upload/', UploadCSV.as_view(), name='upload_csv'),
    path('status/<str:request_id>/', StatusAPIView.as_view(), name='check_status'),
    path('export/<uuid:request_id>/', ExportCSV.as_view(), name='export_csv'),

]
