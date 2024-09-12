import csv
import os
import uuid
import requests
from io import BytesIO
from PIL import Image
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from image_data.models import ImageProcessingRequest, Product
from .serializers import ImageProcessingRequestSerializer
from django.core.files.storage import default_storage
from rest_framework import status


class UploadCSV(APIView):
    def post(self, request):
        # Get the uploaded CSV file
        csv_file = request.FILES.get('file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            return Response({'error': 'Please upload a valid CSV file.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new processing request record
        request_id = str(uuid.uuid4())
        processing_request = ImageProcessingRequest.objects.create(request_id=request_id, status='processing')

        # Read and parse the CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        next(reader)  # Skip header row

        headers = {'User-Agent': 'image_data'}

        # Ensure the processed_images directory exists
        output_directory = default_storage.path('processed_images')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        total_rows = 0
        processed_rows = 0
        errors = []

        for row in reader:
            total_rows += 1
            try:
                # Unpack the row data
                serial_number, product_name, input_image_urls = row[:3]
                product = Product.objects.create(
                    request=processing_request,
                    serial_number=int(serial_number),
                    product_name=product_name,
                    input_image_urls=input_image_urls
                )

                # Process images
                output_urls = []
                for url in input_image_urls.split(','):
                    try:
                        # Download the image
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()

                        # Open and resize the image
                        img = Image.open(BytesIO(response.content))
                        img = img.resize((img.width // 2, img.height // 2))

                        # Save the image
                        output_filename = f'{uuid.uuid4()}.jpg'
                        output_path = os.path.join(output_directory, output_filename)
                        img.save(output_path)
                        output_url = request.build_absolute_uri(
                            default_storage.url(f'processed_images/{output_filename}'))
                        output_urls.append(output_url)

                    except requests.RequestException as e:
                        errors.append(f"Error processing image from URL {url}: {e}")
                        continue

                # Save the output image URLs to the database
                product.output_image_urls = ','.join(output_urls)
                product.save()
                processed_rows += 1

            except ValueError as e:
                errors.append(f"Error unpacking row {row}: {e}")
                continue  # Skip this row if there's an error

        # Update the processing request status
        processing_request.status = 'completed'
        processing_request.save()

        response_text = f"Processing completed. Total rows: {total_rows}, Processed rows: {processed_rows}."
        if errors:
            response_text += f" Errors: {', '.join(errors)}"

        return Response({'request_id': request_id, 'message': response_text}, status=status.HTTP_201_CREATED)


class StatusAPIView(APIView):
    def get(self, request, request_id):
        try:
            processing_request = ImageProcessingRequest.objects.get(request_id=request_id)
            serializer = ImageProcessingRequestSerializer(processing_request)
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ImageProcessingRequest.DoesNotExist:
            return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)


class ExportCSV(APIView):
    def get(self, request, request_id):
        # Check if the request_id is valid
        processing_request = get_object_or_404(ImageProcessingRequest, request_id=request_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="products_with_output_urls_{request_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Serial Number', 'Product Name', 'Input Image URLs', 'Output Image URLs'])

        # Filter products by request_id
        products = Product.objects.filter(request=processing_request)
        for product in products:
            writer.writerow([
                product.serial_number,
                product.product_name,
                product.input_image_urls,
                product.output_image_urls
            ])

        return response


