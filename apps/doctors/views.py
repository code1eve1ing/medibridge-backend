import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsAdmin, IsDoctor
from apps.notifications.services import send_email
from rest_framework.permissions import AllowAny

from .models import DoctorAvailabilitySlot, DoctorEducation, DoctorInvite, DoctorProfile, Specialization
from .serializers import (
    AdminDoctorListSerializer,
    DoctorAvailabilitySlotSerializer,
    DoctorEducationSerializer,
    DoctorProfileSerializer,
    PublicDoctorSerializer,
    SpecializationSerializer,
)
from .services import get_available_slots


@api_view(["GET", "PATCH"])
@permission_classes([IsDoctor])
def doctor_profile(request):
    profile = getattr(request.user, "doctor_profile", None)
    if profile is None:
        return Response(
            {"error": {"code": "profile_not_found", "message": "Doctor profile not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    if request.method == "GET":
        return Response(DoctorProfileSerializer(profile).data)
    serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsDoctor])
def doctor_education_list(request):
    profile = request.user.doctor_profile
    if request.method == "GET":
        return Response(DoctorEducationSerializer(profile.education.all(), many=True).data)
    serializer = DoctorEducationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(doctor=profile)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsDoctor])
def doctor_education_detail(request, pk):
    try:
        entry = DoctorEducation.objects.get(pk=pk, doctor=request.user.doctor_profile)
    except DoctorEducation.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    if request.method == "DELETE":
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = DoctorEducationSerializer(entry, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsDoctor])
def doctor_slots_list(request):
    profile = request.user.doctor_profile
    if request.method == "GET":
        return Response(DoctorAvailabilitySlotSerializer(profile.slots.all(), many=True).data)
    serializer = DoctorAvailabilitySlotSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    # Idempotency: same doctor + same slot identity already exists → return existing.
    dup_filter = dict(
        doctor=profile,
        slot_type=d["slot_type"],
        start_time=d["start_time"],
        end_time=d["end_time"],
        is_active=True,
    )
    if d["slot_type"] == "recurring_weekly":
        dup_filter["day_of_week"] = d.get("day_of_week")
    else:
        dup_filter["specific_date"] = d.get("specific_date")
    existing = DoctorAvailabilitySlot.objects.filter(**dup_filter).first()
    if existing:
        return Response(DoctorAvailabilitySlotSerializer(existing).data, status=status.HTTP_200_OK)
    serializer.save(doctor=profile)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsDoctor])
def doctor_slot_detail(request, pk):
    try:
        slot = DoctorAvailabilitySlot.objects.get(pk=pk, doctor=request.user.doctor_profile)
    except DoctorAvailabilitySlot.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    if request.method == "DELETE":
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = DoctorAvailabilitySlotSerializer(slot, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# --- Public endpoints ---

@api_view(["GET"])
@permission_classes([AllowAny])
def public_specializations(request):
    return Response(SpecializationSerializer(Specialization.objects.all(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_doctor_list(request):
    qs = (
        DoctorProfile.objects
        .filter(is_verified=True, is_available=True)
        .prefetch_related("specializations", "education")
    )
    specialization = request.query_params.get("specialization")
    if specialization:
        qs = qs.filter(specializations__slug=specialization)
    language = request.query_params.get("language")
    if language:
        qs = qs.filter(languages__icontains=language)
    return Response(PublicDoctorSerializer(qs.distinct(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_doctor_detail(request, slug):
    try:
        profile = (
            DoctorProfile.objects
            .filter(is_verified=True, is_available=True)
            .prefetch_related("specializations", "education")
            .get(slug=slug)
        )
    except DoctorProfile.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Doctor not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PublicDoctorSerializer(profile).data)


# --- Patient endpoint ---

@api_view(["GET"])
@permission_classes([AllowAny])
def patient_available_slots(request, doctor_id):
    from apps.core.permissions import IsPatient
    if not IsPatient().has_permission(request, None):
        return Response(
            {"error": {"code": "permission_denied", "message": "Patients only."}},
            status=status.HTTP_403_FORBIDDEN,
        )
    try:
        profile = DoctorProfile.objects.get(pk=doctor_id, is_verified=True, is_available=True)
    except DoctorProfile.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Doctor not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({"slots": get_available_slots(profile)})


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_doctor_list(request):
    qs = DoctorProfile.objects.select_related("user").prefetch_related("specializations")
    is_verified = request.query_params.get("is_verified")
    if is_verified is not None:
        qs = qs.filter(is_verified=is_verified.lower() == "true")
    return Response(AdminDoctorListSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_doctor_invite(request):
    email = request.data.get("email", "").strip()
    if not email:
        return Response(
            {"error": {"code": "validation_error", "message": "Email is required."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invite = DoctorInvite.objects.create(
        email=email,
        token=secrets.token_hex(32),
        invited_by=request.user,
        expires_at=timezone.now() + timedelta(days=7),
    )

    signup_url = f"{settings.SITE_FRONTEND_URL}/auth/signup/doctor/{invite.token}"
    send_email(
        to_email=email,
        subject="You've been invited to join MediBridge as a doctor",
        template_name="doctor_invite",
        context={"invite": invite, "signup_url": signup_url, "invited_by": request.user},
        context_type="doctor_invite",
        context_id=invite.id,
    )

    AuditLog.objects.create(
        actor=request.user,
        action="doctor.invited",
        target_type="DoctorInvite",
        target_id=invite.id,
        metadata={"email": email},
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"message": f"Invitation sent to {email}."}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_doctor_verify(request, pk):
    try:
        profile = DoctorProfile.objects.select_related("user").get(pk=pk)
    except DoctorProfile.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Doctor not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.is_verified = True
    profile.save(update_fields=["is_verified", "updated_at"])

    AuditLog.objects.create(
        actor=request.user,
        action="doctor.verified",
        target_type="DoctorProfile",
        target_id=profile.id,
        metadata={"doctor_email": profile.user.email},
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"message": "Doctor verified successfully."})
