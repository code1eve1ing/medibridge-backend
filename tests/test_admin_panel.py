"""Phase 11 — Admin panel tests."""
import pytest
from datetime import timedelta
from django.utils import timezone


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(email="panel_admin@test.local", password="pass",
                                    role="admin", is_email_verified=True)

@pytest.fixture
def patient_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(email="panel_patient@test.local", password="pass",
                                    role="patient", is_email_verified=True)

@pytest.fixture
def doctor_user(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="panel_doctor@test.local", password="pass",
                                 role="doctor", is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="Doc", last_name="Smith",
                                  is_verified=True, is_available=True)
    return u

@pytest.fixture
def unverified_doctor(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="panel_unverified@test.local", password="pass",
                                 role="doctor", is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="New", last_name="Doc",
                                  is_verified=False, is_available=False)
    return u

@pytest.fixture
def pending_intake(db, patient_user):
    from apps.consultations.models import SymptomIntake
    return SymptomIntake.objects.create(
        patient=patient_user.patient_profile,
        chief_complaint="Headache",
        symptoms="Severe headache",
        duration="2 days",
        severity="moderate",
        status="pending",
    )

@pytest.fixture
def appointment_today(db, patient_user, doctor_user):
    from apps.consultations.models import Appointment
    now = timezone.now()
    return Appointment.objects.create(
        patient=patient_user.patient_profile,
        doctor=doctor_user.doctor_profile,
        scheduled_start=now.replace(hour=10, minute=0, second=0, microsecond=0),
        scheduled_end=now.replace(hour=10, minute=30, second=0, microsecond=0),
        status="scheduled",
        payment_ref="DUMMY-TODAY",
        meeting_link="https://meet.jit.si/test",
    )

@pytest.fixture
def confirmed_surgery_booking(db, patient_user):
    from apps.hospitals.models import Hospital, SurgeryPackage
    from apps.surgery.models import SurgeryPackageBooking
    h = Hospital.objects.create(name="H1", city="Mumbai", state="MH",
                                 country="India", description="d")
    pkg = SurgeryPackage.objects.create(
        hospital=h, name="Knee Pkg", surgery_type="knee_replacement",
        description="d", total_duration_days=14, hospital_stay_days=5,
        recovery_stay_days=9, price_usd="3500.00",
    )
    return SurgeryPackageBooking.objects.create(
        patient=patient_user.patient_profile,
        package=pkg,
        tentative_date="2027-06-01",
        total_amount_usd="3500.00",
        status="confirmed",
        payment_ref="DUMMY-SURG",
    )

def login(client, user):
    client.post("/api/v1/auth/login", {"email": user.email, "password": "pass"},
                content_type="application/json")


# ── Dashboard KPIs ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dashboard_returns_kpis(client, admin_user, pending_intake, appointment_today,
                                 confirmed_surgery_booking, doctor_user, unverified_doctor):
    login(client, admin_user)
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["pending_intakes"] >= 1
    assert data["appointments_today"] >= 1
    assert data["unverified_doctors"] >= 1
    assert data["active_doctors"] >= 1
    assert data["confirmed_surgery_revenue_usd"] >= 3500.0
    assert "new_surgery_bookings_7d" in data


@pytest.mark.django_db
def test_dashboard_requires_admin(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 403


# ── Bookings list ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_admin_bookings_returns_both_types(client, admin_user, appointment_today,
                                            confirmed_surgery_booking):
    login(client, admin_user)
    res = client.get("/api/v1/admin/bookings")
    assert res.status_code == 200
    types = {b["type"] for b in res.json()}
    assert "consultation" in types
    assert "surgery" in types


@pytest.mark.django_db
def test_admin_bookings_filter_by_type_consultation(client, admin_user, appointment_today,
                                                     confirmed_surgery_booking):
    login(client, admin_user)
    res = client.get("/api/v1/admin/bookings?type=consultation")
    assert res.status_code == 200
    assert all(b["type"] == "consultation" for b in res.json())


@pytest.mark.django_db
def test_admin_bookings_filter_by_type_surgery(client, admin_user, appointment_today,
                                                confirmed_surgery_booking):
    login(client, admin_user)
    res = client.get("/api/v1/admin/bookings?type=surgery")
    assert res.status_code == 200
    assert all(b["type"] == "surgery" for b in res.json())


@pytest.mark.django_db
def test_admin_bookings_filter_by_status(client, admin_user, appointment_today):
    login(client, admin_user)
    res = client.get("/api/v1/admin/bookings?type=consultation&status=scheduled")
    assert res.status_code == 200
    assert all(b["status"] == "scheduled" for b in res.json())


@pytest.mark.django_db
def test_bookings_requires_admin(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/admin/bookings")
    assert res.status_code == 403


# ── Audit log ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_audit_log_returns_entries(client, admin_user):
    from apps.core.models import AuditLog
    AuditLog.objects.create(
        actor=admin_user,
        action="doctor.verified",
        target_type="DoctorProfile",
        target_id=1,
        metadata={"test": True},
    )
    login(client, admin_user)
    res = client.get("/api/v1/admin/audit-log")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert data["count"] >= 1
    entry = data["results"][0]
    assert "action" in entry
    assert "actor_email" in entry
    assert "created_at" in entry


@pytest.mark.django_db
def test_audit_log_requires_admin(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/admin/audit-log")
    assert res.status_code == 403


@pytest.mark.django_db
def test_booking_confirmed_creates_audit_log(client, patient_user, doctor_user):
    from apps.core.models import AuditLog
    login(client, patient_user)
    now = timezone.now()
    start = (now + timedelta(days=7)).replace(hour=14, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
    }, content_type="application/json")
    assert AuditLog.objects.filter(action="booking.confirmed").exists()
