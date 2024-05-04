from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from store_monitor.views import generate_report
from store_monitor.models import Report
from django.http import Http404
from django.shortcuts import get_object_or_404
import uuid


class GenerateReport(APIView):
    """
    API endpoint for generating a report.

    This endpoint allows users to generate a report by sending a GET request.
    The report generation is initiated by creating a new `Report` object with the status set to 'Running'.
    The report generation is performed asynchronously using the `generate_report` task.
    If the report generation is successful, the response will include the `report_id`.
    If an error occurs during the report generation, the error message will be returned in the response.
    """

    def get(self, request):
        # Initiate report generation
        report = Report.objects.create(status='Running')
        try:
            generate_report.delay(report.id)
            return Response({"report_id": report.id}, status=status.HTTP_200_OK)
        except Exception as e:
            report.delete()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReport(APIView):
    """
    API view to retrieve a report based on the provided report ID.

    Request Parameters:
        - report_id (str): The ID of the report to retrieve.

    Returns:
        - If the report ID is not provided or invalid, returns a 400 Bad Request response with an error message.
        - If the report is still running, returns a 200 OK response with a status message.
        - If the report is completed, returns a 200 OK response with the report's CSV URL.
    """
    def post(self, request):
        input_id = request.data.get('report_id')

        if not input_id:
            return Response({'error': 'No Valid inputs', "input parameter": {"report_id": ""}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid.UUID(input_id)  # This will raise a ValueError if input_id is not a valid UUID
        except ValueError:
            return Response({'error': 'Invalid UUID format provided.'}, status=status.HTTP_400_BAD_REQUEST)

        report = get_object_or_404(Report, id=input_id)

        if report.status == 'Running':
            return Response({'status': 'Running'}, status=status.HTTP_200_OK)

        # If the report is completed, send the CSV URL
        return Response({
            'status': 'Complete',
            'report': request.build_absolute_uri(report.file.url)
        }, status=status.HTTP_200_OK)
