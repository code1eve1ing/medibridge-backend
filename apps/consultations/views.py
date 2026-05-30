import secrets
from datetime import timedelta

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsAdmin, IsDoctor, IsPatient
from apps.core.services.pdf import render_pdf
from apps.notifications.services import send_email

from .models import Appointment, Prescription, PrescriptionMedicine, PrescribedTest, SymptomIntake
from .serializers import (
    AdminIntakeSerializer, AdminMatchSerializer, PatientIntakeSerializer,
    AppointmentCreateSerializer, AppointmentSerializer,
    AppointmentStatusSerializer, DoctorAppointmentSerializer,
    FollowUpCreateSerializer,
    PrescriptionReadSerializer, PrescriptionWriteSerializer,
    PatientPrescriptionListSerializer,
)


@api_view(["GET", "POST"])
@permission_classes([IsPatient])
def patient_intake_list(request):
    profile = request.user.patient_profile
    if request.method == "GET":
        intakes = SymptomIntake.objects.filter(patient=profile).select_related(
            "preferred_doctor", "matched_doctor"
        ).prefetch_related("matched_doctor__specializations")
        return Response(PatientIntakeSerializer(intakes, many=True).data)

    serializer = PatientIntakeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    intake = serializer.save(patient=profile)

    # Notify admin
    try:
        from django.conf import settings
        send_email(
            to_email=settings.ADMIN_NOTIFICATION_EMAIL,
            subject="New symptom intake submitted",
            template_name="intake_submitted",
            context={"intake": intake, "patient": profile},
            context_type="SymptomIntake",
            context_id=intake.id,
        )
    except Exception:
        pass

    return Response(PatientIntakeSerializer(intake).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsPatient])
def patient_intake_cancel(request, pk):
    try:
        intake = SymptomIntake.objects.get(pk=pk, patient=request.user.patient_profile)
    except SymptomIntake.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if intake.status == "matched":
        return Response(
            {"error": {"code": "invalid_status", "message": "Matched intakes cannot be cancelled."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if intake.status == "cancelled":
        return Response(
            {"error": {"code": "invalid_status", "message": "Already cancelled."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    intake.status = "cancelled"
    intake.save(update_fields=["status", "updated_at"])
    return Response(PatientIntakeSerializer(intake).data)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_intake_list(request):
    qs = SymptomIntake.objects.select_related(
        "patient__user",
        "preferred_doctor",
        "matched_doctor",
        "matched_by",
    ).prefetch_related(
        "preferred_doctor__specializations",
        "matched_doctor__specializations",
    )

    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)

    return Response(AdminIntakeSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_intake_match(request, pk):
    try:
        intake = SymptomIntake.objects.select_related("patient__user").get(pk=pk)
    except SymptomIntake.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if intake.status == "cancelled":
        return Response(
            {"error": {"code": "invalid_status", "message": "Cannot match a cancelled intake."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = AdminMatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    doctor = serializer.validated_data["doctor_id"]
    notes = serializer.validated_data.get("admin_notes", "")

    # Idempotency: already matched to the same doctor, no re-work needed
    if intake.status == "matched" and intake.matched_doctor_id == doctor.id:
        return Response(AdminIntakeSerializer(intake).data)

    # Cancel any previously auto-created proposed appointments for this intake
    # (handles legacy records and re-match scenarios)
    Appointment.objects.filter(intake=intake, status="proposed").update(status="cancelled")

    intake.matched_doctor = doctor
    intake.matched_by = request.user
    intake.matched_at = timezone.now()
    intake.status = "matched"
    if notes:
        intake.admin_notes = notes
    intake.save()

    AuditLog.objects.create(
        actor=request.user,
        action="intake.matched",
        target_type="SymptomIntake",
        target_id=intake.id,
        metadata={"doctor_id": doctor.id, "patient_email": intake.patient.user.email},
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    # Notify patient to book their slot with the matched doctor
    try:
        send_email(
            to_email=intake.patient.user.email,
            subject="Your consultation request has been matched",
            template_name="intake_matched",
            context={"intake": intake, "doctor": doctor},
            context_type="SymptomIntake",
            context_id=intake.id,
        )
    except Exception:
        pass

    # Notify doctor about the new patient intake
    try:
        send_email(
            to_email=doctor.user.email,
            subject="New patient assigned to you",
            template_name="intake_matched_doctor",
            context={"doctor": doctor, "patient": intake.patient, "intake": intake},
            context_type="SymptomIntake",
            context_id=intake.id,
        )
    except Exception:
        pass

    return Response(AdminIntakeSerializer(intake).data)


# ── Phase 6: Appointments ────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsPatient])
def patient_appointment_list(request):
    profile = request.user.patient_profile
    if request.method == "GET":
        qs = Appointment.objects.filter(patient=profile).select_related("doctor")
        return Response(AppointmentSerializer(qs, many=True).data)

    ser = AppointmentCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data
    doctor = d["doctor_id"]
    start, end = d["scheduled_start"], d["scheduled_end"]

    with transaction.atomic():
        # Idempotency: if this patient already booked this doctor at this exact slot,
        # return the existing appointment instead of creating a duplicate (handles
        # double-click, back-navigation, and accidental refresh re-submits).
        existing = Appointment.objects.select_for_update().filter(
            patient=profile,
            doctor=doctor,
            scheduled_start=start,
            scheduled_end=end,
            status__in=["proposed", "scheduled", "in_progress"],
        ).first()
        if existing:
            return Response(AppointmentSerializer(existing).data, status=status.HTTP_200_OK)

        # Doctor-side conflict: anyone else already in this slot? Include "proposed"
        # so admin-matched appointments aren't ignored.
        conflict = Appointment.objects.select_for_update().filter(
            doctor=doctor,
            status__in=["proposed", "scheduled", "in_progress"],
            scheduled_start__lt=end,
            scheduled_end__gt=start,
        ).exists()
        if conflict:
            return Response(
                {"error": {"code": "slot_taken", "message": "That slot is no longer available."}},
                status=status.HTTP_409_CONFLICT,
            )
        appt = Appointment.objects.create(
            patient=profile,
            doctor=doctor,
            intake=d.get("intake_id"),
            scheduled_start=start,
            scheduled_end=end,
            notes=d.get("notes", ""),
            payment_ref=f"DUMMY-{secrets.token_hex(6).upper()}",
            meeting_link=f"https://meet.jit.si/medibridge-{secrets.token_hex(8)}",
        )

    # Confirmation emails (best-effort)
    ctx = {"appointment": appt, "doctor": appt.doctor, "patient": appt.patient,
           "meeting_link": appt.meeting_link}
    try:
        send_email(to_email=appt.patient.user.email,
                   subject="Your appointment is confirmed",
                   template_name="appointment_confirmed_patient",
                   context=ctx, context_type="Appointment", context_id=appt.id)
    except Exception:
        pass
    try:
        send_email(to_email=appt.doctor.user.email,
                   subject="New appointment scheduled",
                   template_name="appointment_confirmed_doctor",
                   context=ctx, context_type="Appointment", context_id=appt.id)
    except Exception:
        pass

    AuditLog.objects.create(
        actor=request.user,
        action="booking.confirmed",
        target_type="Appointment",
        target_id=appt.id,
        metadata={"doctor_id": doctor.id, "patient_email": profile.user.email, "payment_ref": appt.payment_ref},
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response(AppointmentSerializer(appt).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsPatient])
def patient_appointment_cancel(request, pk):
    try:
        appt = Appointment.objects.get(pk=pk, patient=request.user.patient_profile)
    except Appointment.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)
    if appt.status not in ("scheduled",):
        return Response(
            {"error": {"code": "invalid_status", "message": "Only scheduled appointments can be cancelled."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    appt.status = "cancelled"
    appt.save(update_fields=["status", "updated_at"])
    return Response(AppointmentSerializer(appt).data)


@api_view(["GET"])
@permission_classes([IsDoctor])
def doctor_appointment_list(request):
    qs = (
        Appointment.objects
        .filter(doctor=request.user.doctor_profile)
        .select_related("patient__user")
    )
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response(DoctorAppointmentSerializer(qs, many=True).data)


@api_view(["PATCH"])
@permission_classes([IsDoctor])
def doctor_appointment_status(request, pk):
    try:
        appt = Appointment.objects.get(pk=pk, doctor=request.user.doctor_profile)
    except Appointment.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    ser = AppointmentStatusSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    new_status = ser.validated_data["status"]

    valid_transitions = {
        "scheduled": ["in_progress", "no_show"],
        "in_progress": ["completed"],
    }
    if new_status not in valid_transitions.get(appt.status, []):
        return Response(
            {"error": {"code": "invalid_transition",
                       "message": f"Cannot move from '{appt.status}' to '{new_status}'."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    appt.status = new_status
    fields = ["status", "updated_at"]
    if new_status == "completed":
        appt.completed_at = timezone.now()
        fields.append("completed_at")
    appt.save(update_fields=fields)
    return Response(DoctorAppointmentSerializer(appt).data)


@api_view(["GET"])
@permission_classes([IsDoctor])
def doctor_appointment_patient_profile(request, pk):
    from apps.patients.serializers import PatientProfileForDoctorSerializer
    try:
        appt = Appointment.objects.select_related(
            "patient__user"
        ).prefetch_related("patient__medical_reports").get(
            pk=pk, doctor=request.user.doctor_profile
        )
    except Appointment.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "Not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PatientProfileForDoctorSerializer(appt.patient).data)


@api_view(["POST"])
@permission_classes([IsPatient])
def dev_dummy_payment(request):
    # Dummy payment — never processes real money; blocked at the gateway config layer in prod
    return Response({"payment_ref": f"DUMMY-{secrets.token_hex(6).upper()}"})


# ── Phase 7: Prescriptions ───────────────────────────────────────────────────

def _can_edit(appt):
    """Within 24h of appointment completion."""
    if not appt.completed_at:
        return False
    return timezone.now() < appt.completed_at + timedelta(hours=24)


@api_view(["GET", "POST"])
@permission_classes([IsDoctor])
def doctor_prescription(request, pk):
    try:
        appt = Appointment.objects.select_related(
            "doctor", "patient__user"
        ).get(pk=pk, doctor=request.user.doctor_profile)
    except Appointment.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    if request.method == "GET":
        if not hasattr(appt, "prescription"):
            return Response({"error": {"code": "not_found", "message": "No prescription yet."}}, status=404)
        return Response(PrescriptionReadSerializer(appt.prescription).data)

    # POST — create
    if appt.status != "completed":
        return Response(
            {"error": {"code": "invalid_status", "message": "Can only write prescription for completed appointments."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if hasattr(appt, "prescription"):
        return Response(
            {"error": {"code": "already_exists", "message": "Prescription already exists. Use PATCH to edit."}},
            status=status.HTTP_409_CONFLICT,
        )

    ser = PrescriptionWriteSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    prescription = ser.save(appointment=appt)

    # Notify patient
    try:
        send_email(
            to_email=appt.patient.user.email,
            subject="Your prescription is ready",
            template_name="prescription_ready",
            context={"prescription": prescription, "appointment": appt, "doctor": appt.doctor},
            context_type="Prescription",
            context_id=prescription.id,
        )
    except Exception:
        pass

    return Response(PrescriptionReadSerializer(prescription).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsDoctor])
def doctor_prescription_edit(request, pk):
    try:
        prescription = Prescription.objects.select_related(
            "appointment__doctor", "appointment__patient__user"
        ).get(pk=pk, appointment__doctor=request.user.doctor_profile)
    except Prescription.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    if not _can_edit(prescription.appointment):
        return Response(
            {"error": {"code": "edit_window_closed", "message": "Prescription can only be edited within 24 hours of appointment completion."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    ser = PrescriptionWriteSerializer(prescription, data=request.data)
    ser.is_valid(raise_exception=True)
    # Clear cached PDF — content changed
    if prescription.pdf_file:
        prescription.pdf_file.delete(save=False)
    prescription = ser.save()
    return Response(PrescriptionReadSerializer(prescription).data)


@api_view(["GET"])
@permission_classes([IsPatient])
def patient_prescription_list(request):
    prescriptions = Prescription.objects.filter(
        appointment__patient=request.user.patient_profile
    ).select_related("appointment__doctor")
    return Response(PatientPrescriptionListSerializer(prescriptions, many=True).data)


@api_view(["GET"])
@permission_classes([IsPatient])
def patient_prescription_detail(request, pk):
    try:
        prescription = Prescription.objects.select_related(
            "appointment__doctor", "appointment__patient__user"
        ).prefetch_related("medicines", "tests").get(
            pk=pk, appointment__patient=request.user.patient_profile
        )
    except Prescription.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)
    return Response(PrescriptionReadSerializer(prescription).data)


@api_view(["GET"])
@permission_classes([IsPatient])
def patient_prescription_pdf(request, pk):
    try:
        prescription = Prescription.objects.select_related(
            "appointment__doctor", "appointment__patient"
        ).prefetch_related("medicines", "tests").get(
            pk=pk, appointment__patient=request.user.patient_profile
        )
    except Prescription.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    # Serve cached PDF if available and content not changed
    if prescription.pdf_file:
        try:
            pdf_bytes = prescription.pdf_file.read()
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="prescription_{pk}.pdf"'
            return response
        except Exception:
            pass

    # Generate PDF
    pdf_bytes = render_pdf("pdf/prescription.html", {"prescription": prescription})
    # Cache it
    from django.core.files.base import ContentFile
    prescription.pdf_file.save(f"rx_{pk}.pdf", ContentFile(pdf_bytes), save=True)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="prescription_{pk}.pdf"'
    return response


# ── Phase 8: Follow-up Consultations ────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsDoctor])
def doctor_follow_up(request, pk):
    try:
        appt = Appointment.objects.select_related(
            "patient__user", "doctor"
        ).get(pk=pk, doctor=request.user.doctor_profile)
    except Appointment.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    if appt.status != "completed":
        return Response(
            {"error": {"code": "invalid_status", "message": "Follow-ups can only be proposed for completed appointments."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ser = FollowUpCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data
    start, end = d["scheduled_start"], d["scheduled_end"]
    fee_waived = d.get("fee_waived", False)

    with transaction.atomic():
        conflict = Appointment.objects.select_for_update().filter(
            doctor=appt.doctor,
            status__in=["proposed", "scheduled", "in_progress"],
            scheduled_start__lt=end,
            scheduled_end__gt=start,
        ).exists()
        if conflict:
            return Response(
                {"error": {"code": "slot_taken", "message": "That slot is not available."}},
                status=status.HTTP_409_CONFLICT,
            )
        follow_up = Appointment.objects.create(
            patient=appt.patient,
            doctor=appt.doctor,
            parent_appointment=appt,
            scheduled_start=start,
            scheduled_end=end,
            status="proposed",
            fee_waived=fee_waived,
            meeting_link=f"https://meet.jit.si/medibridge-{secrets.token_hex(8)}",
        )

    try:
        send_email(
            to_email=appt.patient.user.email,
            subject="Follow-up consultation proposed",
            template_name="follow_up_proposed",
            context={"follow_up": follow_up, "appointment": appt, "doctor": appt.doctor},
            context_type="Appointment",
            context_id=follow_up.id,
        )
    except Exception:
        pass

    return Response(AppointmentSerializer(follow_up).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsPatient])
def patient_confirm_follow_up(request, pk):
    try:
        follow_up = Appointment.objects.get(
            pk=pk,
            patient=request.user.patient_profile,
            status="proposed",
        )
    except Appointment.DoesNotExist:
        return Response({"error": {"code": "not_found", "message": "Not found."}}, status=404)

    follow_up.status = "scheduled"
    fields = ["status", "updated_at"]
    if not follow_up.fee_waived:
        follow_up.payment_ref = f"DUMMY-{secrets.token_hex(6).upper()}"
        fields.append("payment_ref")
    follow_up.save(update_fields=fields)
    return Response(AppointmentSerializer(follow_up).data)
