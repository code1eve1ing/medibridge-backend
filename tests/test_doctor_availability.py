import pytest
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

from freezegun import freeze_time
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.doctors.models import DoctorAvailabilitySlot, DoctorProfile, Specialization
from apps.doctors.services import get_available_slots


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(email="doc@test.com", password="Testpass123!", role="doctor")
    user.is_email_verified = True
    user.save()
    DoctorProfile.objects.create(
        user=user, first_name="Jane", last_name="Doe",
        timezone="Asia/Kolkata", consultation_duration_min=30,
        is_verified=True, is_available=True,
    )
    return user


@pytest.fixture
def unverified_doctor(db):
    user = User.objects.create_user(email="unverified@test.com", password="Testpass123!", role="doctor")
    user.is_email_verified = True
    user.save()
    DoctorProfile.objects.create(user=user, first_name="Bob", last_name="Jones", is_verified=False)
    return user


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(email="patient@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


def login(client, user, password="Testpass123!"):
    res = client.post("/api/v1/auth/login", {"email": user.email, "password": password}, format="json")
    client.cookies = res.cookies
    return client


# --- Slot CRUD ---

@pytest.mark.django_db
def test_doctor_create_recurring_slot(client, doctor_user):
    login(client, doctor_user)
    res = client.post("/api/v1/doctor/slots", {
        "slot_type": "recurring_weekly",
        "day_of_week": 0,
        "start_time": "09:00",
        "end_time": "12:00",
    }, format="json")
    assert res.status_code == 201
    assert DoctorAvailabilitySlot.objects.filter(doctor=doctor_user.doctor_profile, day_of_week=0).exists()


@pytest.mark.django_db
def test_doctor_create_specific_date_slot(client, doctor_user):
    login(client, doctor_user)
    res = client.post("/api/v1/doctor/slots", {
        "slot_type": "specific_date",
        "specific_date": "2026-06-15",
        "start_time": "10:00",
        "end_time": "13:00",
    }, format="json")
    assert res.status_code == 201


@pytest.mark.django_db
def test_doctor_slot_end_before_start_rejected(client, doctor_user):
    login(client, doctor_user)
    res = client.post("/api/v1/doctor/slots", {
        "slot_type": "recurring_weekly",
        "day_of_week": 1,
        "start_time": "15:00",
        "end_time": "09:00",
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_doctor_delete_slot(client, doctor_user):
    login(client, doctor_user)
    slot = DoctorAvailabilitySlot.objects.create(
        doctor=doctor_user.doctor_profile,
        slot_type="recurring_weekly",
        day_of_week=2,
        start_time=time(9, 0),
        end_time=time(12, 0),
    )
    res = client.delete(f"/api/v1/doctor/slots/{slot.id}")
    assert res.status_code == 204
    assert not DoctorAvailabilitySlot.objects.filter(id=slot.id).exists()


@pytest.mark.django_db
def test_patient_cannot_manage_slots(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/doctor/slots")
    assert res.status_code == 403


# --- Public endpoints ---

@pytest.mark.django_db
def test_public_specializations(client, db):
    Specialization.objects.create(name="Cardiology", slug="cardiology")
    res = client.get("/api/v1/public/specializations")
    assert res.status_code == 200
    assert any(s["slug"] == "cardiology" for s in res.json())


@pytest.mark.django_db
def test_public_doctor_list_only_verified(client, doctor_user, unverified_doctor):
    res = client.get("/api/v1/public/doctors")
    assert res.status_code == 200
    slugs = [d["slug"] for d in res.json()]
    assert doctor_user.doctor_profile.slug in slugs
    assert unverified_doctor.doctor_profile.slug not in slugs


@pytest.mark.django_db
def test_public_doctor_list_filter_by_specialization(client, doctor_user, db):
    spec = Specialization.objects.create(name="Neurology", slug="neurology")
    doctor_user.doctor_profile.specializations.add(spec)
    res = client.get("/api/v1/public/doctors?specialization=neurology")
    assert res.status_code == 200
    assert any(d["slug"] == doctor_user.doctor_profile.slug for d in res.json())
    res2 = client.get("/api/v1/public/doctors?specialization=cardiology")
    assert all(d["slug"] != doctor_user.doctor_profile.slug for d in res2.json())


@pytest.mark.django_db
def test_public_doctor_detail(client, doctor_user):
    slug = doctor_user.doctor_profile.slug
    res = client.get(f"/api/v1/public/doctors/{slug}")
    assert res.status_code == 200
    assert res.json()["slug"] == slug


@pytest.mark.django_db
def test_public_doctor_detail_unverified_returns_404(client, unverified_doctor):
    slug = unverified_doctor.doctor_profile.slug
    res = client.get(f"/api/v1/public/doctors/{slug}")
    assert res.status_code == 404


# --- Available slots computation ---

@pytest.mark.django_db
@freeze_time("2026-05-05 03:30:00+00:00")  # 09:00 IST on Monday 5 May 2026
def test_recurring_slots_expanded(doctor_user):
    profile = doctor_user.doctor_profile
    # Monday 9:00–10:00 IST → two 30-min chunks
    DoctorAvailabilitySlot.objects.create(
        doctor=profile, slot_type="recurring_weekly",
        day_of_week=0,  # Monday
        start_time=time(9, 0), end_time=time(10, 0),
    )
    slots = get_available_slots(profile, days=14)
    # Should have 2 slots on next Monday (day 7, since current time is already 09:00 IST)
    # and 2 slots on the Monday after (day 14 is outside range, so just 1 Monday within 14 days)
    assert len(slots) >= 2
    # Verify UTC conversion: 9:00 IST = 3:30 UTC
    starts = [s["start"] for s in slots]
    assert any("03:30:00" in s for s in starts)


@pytest.mark.django_db
@freeze_time("2026-05-05 00:00:00+00:00")  # 05:30 IST on Monday 5 May 2026
def test_specific_date_slot_included(doctor_user):
    profile = doctor_user.doctor_profile
    DoctorAvailabilitySlot.objects.create(
        doctor=profile, slot_type="specific_date",
        specific_date=date(2026, 5, 6),  # Tomorrow (Tuesday)
        start_time=time(14, 0), end_time=time(15, 0),
    )
    slots = get_available_slots(profile, days=14)
    assert len(slots) == 2  # Two 30-min chunks
    # 14:00 IST = 08:30 UTC
    assert any("08:30:00" in s["start"] for s in slots)


@pytest.mark.django_db
def test_past_slots_excluded(doctor_user):
    from datetime import datetime, timezone as dt_timezone
    profile = doctor_user.doctor_profile
    # Specific-date slot for yesterday — always outside the forward-looking window
    yesterday = (datetime.now(dt_timezone.utc) - timedelta(days=1)).date()
    DoctorAvailabilitySlot.objects.create(
        doctor=profile, slot_type="specific_date",
        specific_date=yesterday,
        start_time=time(9, 0), end_time=time(10, 0),
    )
    slots = get_available_slots(profile, days=14)
    assert len(slots) == 0


@pytest.mark.django_db
def test_timezone_utc_conversion_correct(doctor_user):
    from datetime import datetime, timezone as dt_timezone
    from zoneinfo import ZoneInfo
    profile = doctor_user.doctor_profile
    # Specific-date slot tomorrow in doctor's timezone (IST = UTC+5:30, no DST)
    tomorrow_ist = (
        datetime.now(dt_timezone.utc) + timedelta(days=1)
    ).astimezone(ZoneInfo("Asia/Kolkata")).date()
    DoctorAvailabilitySlot.objects.create(
        doctor=profile, slot_type="specific_date",
        specific_date=tomorrow_ist,
        start_time=time(9, 0), end_time=time(9, 30),
    )
    slots = get_available_slots(profile, days=3)
    assert len(slots) == 1
    # IST is always UTC+5:30: 09:00 IST → 03:30 UTC, 09:30 IST → 04:00 UTC
    assert "03:30:00" in slots[0]["start"]
    assert "04:00:00" in slots[0]["end"]


# --- Available slots endpoint (patient only) ---

@pytest.mark.django_db
def test_available_slots_requires_patient(client, doctor_user, unverified_doctor):
    profile = doctor_user.doctor_profile
    # Unauthenticated
    res = client.get(f"/api/v1/patient/doctors/{profile.id}/available-slots")
    assert res.status_code == 403


@pytest.mark.django_db
def test_available_slots_returns_data(client, doctor_user, patient_user):
    login(client, patient_user)
    profile = doctor_user.doctor_profile
    DoctorAvailabilitySlot.objects.create(
        doctor=profile, slot_type="recurring_weekly",
        day_of_week=0, start_time=time(9, 0), end_time=time(10, 0),
    )
    res = client.get(f"/api/v1/patient/doctors/{profile.id}/available-slots")
    assert res.status_code == 200
    assert "slots" in res.json()
