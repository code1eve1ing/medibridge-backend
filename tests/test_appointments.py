import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consultations.models import Appointment
from apps.doctors.models import DoctorProfile


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(email="patient@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def patient_user2(db):
    user = User.objects.create_user(email="patient2@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(email="doc@test.com", password="Testpass123!", role="doctor")
    user.is_email_verified = True
    user.save()
    DoctorProfile.objects.create(
        user=user, first_name="Jane", last_name="Doe",
        timezone="Asia/Kolkata", consultation_duration_min=30,
        is_verified=True, is_available=True, consultation_fee_usd="50.00",
    )
    return user


def login(client, user):
    res = client.post("/api/v1/auth/login", {"email": user.email, "password": "Testpass123!"}, format="json")
    client.cookies = res.cookies


def future_slot(offset_hours=24):
    start = timezone.now() + timedelta(hours=offset_hours)
    end = start + timedelta(minutes=30)
    return start.isoformat(), end.isoformat()


# ── Book ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_book_appointment(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start,
        "scheduled_end": end,
    }, format="json")
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "scheduled"
    assert data["payment_ref"].startswith("DUMMY-")


@pytest.mark.django_db
def test_booking_double_book_rejected(client, patient_user, patient_user2, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")

    login(client, patient_user2)
    res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    assert res.status_code == 409


@pytest.mark.django_db
def test_booking_end_before_start_rejected(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": end,
        "scheduled_end": start,
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_cannot_book(client, doctor_user, db):
    start, end = future_slot()
    res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    assert res.status_code == 401


@pytest.mark.django_db
def test_doctor_cannot_book(client, doctor_user):
    login(client, doctor_user)
    start, end = future_slot()
    res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    assert res.status_code == 403


# ── List ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_lists_own_appointments(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    res = client.get("/api/v1/patient/appointments")
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_patient_cannot_see_other_patient_appointments(client, patient_user, patient_user2, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    login(client, patient_user2)
    res = client.get("/api/v1/patient/appointments")
    assert len(res.json()) == 0


# ── Cancel ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_cancel_scheduled_appointment(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    book_res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    pk = book_res.json()["id"]
    res = client.post(f"/api/v1/patient/appointments/{pk}/cancel")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


@pytest.mark.django_db
def test_patient_cannot_cancel_completed_appointment(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    book_res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    pk = book_res.json()["id"]
    # Force complete via DB
    Appointment.objects.filter(pk=pk).update(status="completed")
    res = client.post(f"/api/v1/patient/appointments/{pk}/cancel")
    assert res.status_code == 400


# ── Doctor views ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_doctor_lists_appointments(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    login(client, doctor_user)
    res = client.get("/api/v1/doctor/appointments")
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_doctor_update_status_valid_transition(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    book_res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    pk = book_res.json()["id"]
    login(client, doctor_user)
    res = client.patch(f"/api/v1/doctor/appointments/{pk}/status", {"status": "in_progress"}, format="json")
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"


@pytest.mark.django_db
def test_doctor_invalid_status_transition_rejected(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    book_res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    pk = book_res.json()["id"]
    login(client, doctor_user)
    # scheduled → completed is invalid (must go through in_progress)
    res = client.patch(f"/api/v1/doctor/appointments/{pk}/status", {"status": "completed"}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_patient_cannot_update_doctor_status(client, patient_user, doctor_user):
    login(client, patient_user)
    start, end = future_slot()
    book_res = client.post("/api/v1/patient/appointments", {
        "doctor_id": doctor_user.doctor_profile.id,
        "scheduled_start": start, "scheduled_end": end,
    }, format="json")
    pk = book_res.json()["id"]
    res = client.patch(f"/api/v1/doctor/appointments/{pk}/status", {"status": "in_progress"}, format="json")
    assert res.status_code == 403


# ── Dummy payment ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dev_payment_returns_ref(client, patient_user):
    login(client, patient_user)
    res = client.post("/api/v1/dev/payment")
    assert res.status_code == 200
    assert res.json()["payment_ref"].startswith("DUMMY-")
