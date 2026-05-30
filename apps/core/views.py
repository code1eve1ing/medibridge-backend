from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.permissions import IsAdmin

from .models import AuditLog


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "timestamp": timezone.now().isoformat()})


# ── Admin: Dashboard KPIs ─────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    from apps.consultations.models import Appointment, SymptomIntake
    from apps.doctors.models import DoctorProfile
    from apps.surgery.models import SurgeryPackageBooking, SurgeryRecommendation

    today = timezone.now().date()
    seven_days_ago = timezone.now() - timedelta(days=7)

    pending_intakes = SymptomIntake.objects.filter(status="pending").count()
    appointments_today = Appointment.objects.filter(
        scheduled_start__date=today,
        status__in=["scheduled", "in_progress", "completed"],
    ).count()
    new_surgery_bookings_7d = SurgeryPackageBooking.objects.filter(
        created_at__gte=seven_days_ago
    ).count()
    unverified_doctors = DoctorProfile.objects.filter(is_verified=False).count()
    active_doctors = DoctorProfile.objects.filter(is_verified=True, is_available=True).count()
    surgery_revenue = SurgeryPackageBooking.objects.filter(
        status="confirmed"
    ).aggregate(total=Sum("total_amount_usd"))["total"] or 0

    consultation_revenue = Appointment.objects.filter(
        status__in=["scheduled", "in_progress", "completed"],
        fee_waived=False,
    ).exclude(payment_ref="").aggregate(
        total=Sum("doctor__consultation_fee_usd")
    )["total"] or 0

    pending_surgery_recs = SurgeryRecommendation.objects.filter(status="pending_admin").count()

    return Response({
        "pending_intakes": pending_intakes,
        "appointments_today": appointments_today,
        "new_surgery_bookings_7d": new_surgery_bookings_7d,
        "unverified_doctors": unverified_doctors,
        "active_doctors": active_doctors,
        "confirmed_surgery_revenue_usd": float(surgery_revenue),
        "consultation_revenue_usd": float(consultation_revenue),
        "pending_surgery_recs": pending_surgery_recs,
    })


# ── Admin: Combined bookings ──────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_bookings(request):
    from apps.consultations.models import Appointment
    from apps.surgery.models import SurgeryPackageBooking

    booking_type = request.query_params.get("type")  # "consultation" | "surgery"
    status_filter = request.query_params.get("status")

    results = []

    if booking_type != "surgery":
        qs = Appointment.objects.select_related("patient__user", "doctor__user").order_by("-created_at")
        if status_filter:
            qs = qs.filter(status=status_filter)
        for a in qs:
            results.append({
                "id": a.id,
                "type": "consultation",
                "status": a.status,
                "patient_email": a.patient.user.email,
                "doctor_email": a.doctor.user.email,
                "scheduled_start": a.scheduled_start.isoformat(),
                "payment_ref": a.payment_ref,
                "meeting_link": a.meeting_link or "",
                "created_at": a.created_at.isoformat(),
            })

    if booking_type != "consultation":
        qs = SurgeryPackageBooking.objects.select_related(
            "patient__user", "package"
        ).order_by("-created_at")
        if status_filter:
            qs = qs.filter(status=status_filter)
        for b in qs:
            results.append({
                "id": b.id,
                "type": "surgery",
                "status": b.status,
                "patient_email": b.patient.user.email,
                "package_name": b.package.name,
                "tentative_date": b.tentative_date.isoformat(),
                "total_amount_usd": str(b.total_amount_usd),
                "payment_ref": b.payment_ref,
                "created_at": b.created_at.isoformat(),
            })

    results.sort(key=lambda x: x["created_at"], reverse=True)
    return Response(results)


# ── Admin: Audit log ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_audit_log(request):
    from rest_framework.pagination import PageNumberPagination

    qs = AuditLog.objects.select_related("actor").order_by("-created_at")

    paginator = PageNumberPagination()
    paginator.page_size = 50
    page = paginator.paginate_queryset(qs, request)

    data = [
        {
            "id": entry.id,
            "actor_email": entry.actor.email if entry.actor else None,
            "action": entry.action,
            "target_type": entry.target_type,
            "target_id": entry.target_id,
            "metadata": entry.metadata,
            "ip_address": entry.ip_address,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in page
    ]
    return paginator.get_paginated_response(data)


# ── Admin: User management ────────────────────────────────────────────────────

def _user_summary(user):
    entry = {
        "id": user.id,
        "email": user.email,
        "role": user.role or "",
        "is_active": user.is_active,
        "is_email_verified": bool(user.is_email_verified),
        "date_joined": user.date_joined.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "first_name": "",
        "last_name": "",
        "phone": "",
    }
    if user.role == "patient":
        try:
            p = user.patient_profile
            entry.update(first_name=p.first_name, last_name=p.last_name,
                         phone=p.phone, country=p.country)
        except Exception:
            pass
    elif user.role == "doctor":
        try:
            d = user.doctor_profile
            entry.update(first_name=d.first_name, last_name=d.last_name,
                         phone=d.phone, is_verified=d.is_verified)
        except Exception:
            pass
    return entry


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_list_users(request):
    from apps.accounts.models import User

    role_filter = request.query_params.get("role", "").strip()
    search = request.query_params.get("search", "").strip()

    qs = User.objects.all().order_by("role", "email")
    if role_filter:
        qs = qs.filter(role=role_filter)
    if search:
        qs = qs.filter(email__icontains=search)

    return Response([_user_summary(u) for u in qs])


@api_view(["GET", "PATCH"])
@permission_classes([IsAdmin])
def admin_user_detail(request, user_id):
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)

    if request.method == "GET":
        entry = _user_summary(user)
        if user.role == "patient":
            try:
                p = user.patient_profile
                entry.update(
                    date_of_birth=str(p.date_of_birth) if p.date_of_birth else None,
                    gender=p.gender, blood_group=p.blood_group,
                    country=p.country, state=p.state, city=p.city,
                    address_line=p.address_line,
                    existing_conditions=p.existing_conditions,
                    allergies=p.allergies, current_medications=p.current_medications,
                    emergency_contact_name=p.emergency_contact_name,
                    emergency_contact_phone=p.emergency_contact_phone,
                )
            except Exception:
                pass
        elif user.role == "doctor":
            try:
                d = user.doctor_profile
                entry.update(
                    bio=d.bio,
                    is_verified=d.is_verified, is_available=d.is_available,
                    years_of_experience=d.years_of_experience,
                    consultation_fee_usd=str(d.consultation_fee_usd) if d.consultation_fee_usd else None,
                    hospital_affiliation=d.hospital_affiliation,
                    medical_council_reg_no=d.medical_council_reg_no,
                    specializations=[{"id": s.id, "name": s.name} for s in d.specializations.all()],
                )
            except Exception:
                pass
        return Response(entry)

    # PATCH — update account + profile fields
    data = request.data

    for field in ("email", "role", "is_active", "is_email_verified"):
        if field in data:
            setattr(user, field, data[field])
    user.save()

    if user.role == "patient":
        try:
            p = user.patient_profile
            for f in ("first_name", "last_name", "phone", "gender", "blood_group",
                      "country", "state", "city", "address_line", "existing_conditions",
                      "allergies", "current_medications",
                      "emergency_contact_name", "emergency_contact_phone"):
                if f in data:
                    setattr(p, f, data[f])
            p.save()
        except Exception:
            pass
    elif user.role == "doctor":
        try:
            d = user.doctor_profile
            for f in ("first_name", "last_name", "phone", "bio", "is_verified",
                      "is_available", "consultation_fee_usd", "years_of_experience",
                      "hospital_affiliation", "medical_council_reg_no"):
                if f in data:
                    setattr(d, f, data[f])
            d.save()
        except Exception:
            pass

    return Response({"message": "User updated."})


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_set_user_password(request, user_id):
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)

    new_password = request.data.get("new_password", "").strip()
    if len(new_password) < 8:
        return Response({"error": "Password must be at least 8 characters."}, status=400)

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return Response({"message": "Password updated successfully."})
