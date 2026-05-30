from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from apps.core.permissions import IsPatient
from .models import PatientProfile, MedicalReport
from .serializers import PatientProfileSerializer, MedicalReportSerializer


@api_view(["GET", "PATCH"])
@permission_classes([IsPatient])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def patient_profile(request):
    try:
        profile = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response(
            {"error": {"code": "profile_not_found", "message": "Patient profile not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(PatientProfileSerializer(profile).data)

    serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsPatient])
@parser_classes([MultiPartParser, FormParser])
def patient_medical_reports(request):
    try:
        profile = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response(
            {"error": {"code": "profile_not_found", "message": "Patient profile not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        reports = profile.medical_reports.all()
        return Response(MedicalReportSerializer(reports, many=True).data)

    serializer = MedicalReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(patient=profile)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsPatient])
def patient_medical_report_delete(request, pk):
    try:
        profile = PatientProfile.objects.get(user=request.user)
        report = MedicalReport.objects.get(pk=pk, patient=profile)
    except (PatientProfile.DoesNotExist, MedicalReport.DoesNotExist):
        return Response(
            {"error": {"code": "not_found", "message": "Report not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    report.file.delete(save=False)
    report.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
