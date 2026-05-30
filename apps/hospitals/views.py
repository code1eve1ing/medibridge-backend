from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsAdmin

from .models import Hospital, SurgeryPackage
from .serializers import HospitalSerializer, SurgeryPackageSerializer


# ── Admin: Hospitals ──────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_hospital_list(request):
    if request.method == "GET":
        return Response(HospitalSerializer(Hospital.objects.all(), many=True).data)

    serializer = HospitalSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    hospital = serializer.save()
    return Response(HospitalSerializer(hospital).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_hospital_detail(request, pk):
    try:
        hospital = Hospital.objects.get(pk=pk)
    except Hospital.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Hospital not found."}}, status=404)

    if request.method == "GET":
        return Response(HospitalSerializer(hospital).data)

    if request.method == "PATCH":
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(HospitalSerializer(hospital).data)

    hospital.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Admin: Surgery Packages ───────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_package_list(request):
    if request.method == "GET":
        qs = SurgeryPackage.objects.select_related("hospital").all()
        return Response(SurgeryPackageSerializer(qs, many=True).data)

    serializer = SurgeryPackageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    package = serializer.save()
    return Response(SurgeryPackageSerializer(package).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_package_detail(request, pk):
    try:
        package = SurgeryPackage.objects.select_related("hospital").get(pk=pk)
    except SurgeryPackage.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Package not found."}}, status=404)

    if request.method == "GET":
        return Response(SurgeryPackageSerializer(package).data)

    if request.method == "PATCH":
        serializer = SurgeryPackageSerializer(package, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SurgeryPackageSerializer(package).data)

    package.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Public: Hospitals ─────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([])
def public_hospital_list(request):
    hospitals = Hospital.objects.filter(is_partner=True)
    return Response(HospitalSerializer(hospitals, many=True).data)


# ── Public: Surgery Packages ──────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([])
def public_package_list(request):
    qs = SurgeryPackage.objects.select_related("hospital").filter(is_active=True)
    surgery_type = request.query_params.get("surgery_type")
    hospital = request.query_params.get("hospital")
    if surgery_type:
        qs = qs.filter(surgery_type=surgery_type)
    if hospital:
        qs = qs.filter(hospital__id=hospital)
    return Response(SurgeryPackageSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([])
def public_package_detail(request, slug):
    try:
        package = SurgeryPackage.objects.select_related("hospital").get(slug=slug, is_active=True)
    except SurgeryPackage.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Package not found."}}, status=404)

    related = SurgeryPackage.objects.select_related("hospital").filter(
        surgery_type=package.surgery_type, is_active=True
    ).exclude(pk=package.pk)[:3]

    data = SurgeryPackageSerializer(package).data
    data["related_packages"] = SurgeryPackageSerializer(related, many=True).data
    return Response(data)
