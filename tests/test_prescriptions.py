"""Phase 7 — Prescription tests."""
import pytest
from datetime import timedelta
from django.utils import timezone


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def patient_user(db):
    from apps.accounts.models import User
    u = User.objects.create_user(email="rx_patient@test.local", password="pass", role="patient",
                                  is_email_verified=True)
    return u

@pytest.fixture
def patient2_user(db):
    from apps.accounts.models import User
    u = User.objects.create_user(email="rx_patient2@test.local", password="pass", role="patient",
                                  is_email_verified=True)
    return u

@pytest.fixture
def doctor_user(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="rx_doctor@test.local", password="pass", role="doctor",
                                  is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="Arjun", last_name="Sharma",
                                  medical_council_reg_no="MC001", is_verified=True, is_available=True)
    return u

@pytest.fixture
def doctor2_user(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="rx_doctor2@test.local", password="pass", role="doctor",
                                  is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="Priya", last_name="Nair",
                                  medical_council_reg_no="MC002", is_verified=True, is_available=True)
    return u

@pytest.fixture
def completed_appt(db, patient_user, doctor_user):
    from apps.consultations.models import Appointment
    now = timezone.now()
    return Appointment.objects.create(
        patient=patient_user.patient_profile,
        doctor=doctor_user.doctor_profile,
        scheduled_start=now - timedelta(hours=2),
        scheduled_end=now - timedelta(hours=1),
        status="completed",
        completed_at=now - timedelta(hours=1),
        payment_ref="DUMMY-TEST",
        meeting_link="https://meet.jit.si/test",
    )

@pytest.fixture
def scheduled_appt(db, patient_user, doctor_user):
    from apps.consultations.models import Appointment
    now = timezone.now()
    return Appointment.objects.create(
        patient=patient_user.patient_profile,
        doctor=doctor_user.doctor_profile,
        scheduled_start=now + timedelta(hours=2),
        scheduled_end=now + timedelta(hours=3),
        status="scheduled",
        payment_ref="DUMMY-TEST2",
        meeting_link="https://meet.jit.si/test2",
    )

def client_login(client, user):
    client.post("/api/v1/auth/login", {"email": user.email, "password": "pass"},
                content_type="application/json")

PAYLOAD = {
    "diagnosis": "Acute bronchitis",
    "general_notes": "Drink plenty of fluids.",
    "follow_up_required": True,
    "follow_up_after_days": 7,
    "medicines": [
        {
            "medicine_name": "Azithromycin",
            "dosage": "500mg",
            "morning": True, "afternoon": False, "evening": False, "night": False,
            "meal_timing": "after_meal",
            "duration_days": 3,
            "instructions": "Take with water",
        }
    ],
    "tests": [
        {"test_name": "Chest X-ray", "urgency": "routine", "instructions": ""}
    ],
}


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_doctor_creates_prescription(client, completed_appt, doctor_user):
    client_login(client, doctor_user)
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                      PAYLOAD, content_type="application/json")
    assert res.status_code == 201
    data = res.json()
    assert data["diagnosis"] == "Acute bronchitis"
    assert len(data["medicines"]) == 1
    assert data["medicines"][0]["medicine_name"] == "Azithromycin"
    assert data["medicines"][0]["morning"] is True
    assert len(data["tests"]) == 1
    assert data["tests"][0]["test_name"] == "Chest X-ray"
    assert data["follow_up_required"] is True
    assert data["follow_up_after_days"] == 7


@pytest.mark.django_db
def test_prescription_diagnosis_only(client, completed_appt, doctor_user):
    """Prescription with no medicines or tests is valid."""
    client_login(client, doctor_user)
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                      {"diagnosis": "Hypertension", "medicines": [], "tests": []},
                      content_type="application/json")
    assert res.status_code == 201
    assert res.json()["medicines"] == []
    assert res.json()["tests"] == []


@pytest.mark.django_db
def test_doctor_cannot_prescribe_for_scheduled_appointment(client, scheduled_appt, doctor_user):
    client_login(client, doctor_user)
    res = client.post(f"/api/v1/doctor/appointments/{scheduled_appt.id}/prescription",
                      PAYLOAD, content_type="application/json")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_status"


@pytest.mark.django_db
def test_doctor_cannot_prescribe_for_other_doctors_appointment(client, completed_appt, doctor2_user):
    client_login(client, doctor2_user)
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                      PAYLOAD, content_type="application/json")
    assert res.status_code == 404


@pytest.mark.django_db
def test_duplicate_prescription_rejected(client, completed_appt, doctor_user):
    client_login(client, doctor_user)
    client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                PAYLOAD, content_type="application/json")
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                      PAYLOAD, content_type="application/json")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "already_exists"


@pytest.mark.django_db
def test_doctor_edits_prescription_within_window(client, completed_appt, doctor_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    updated = {**PAYLOAD, "diagnosis": "Updated diagnosis", "medicines": []}
    res = client.patch(f"/api/v1/doctor/prescriptions/{rx_id}", updated,
                       content_type="application/json")
    assert res.status_code == 200
    assert res.json()["diagnosis"] == "Updated diagnosis"
    assert res.json()["medicines"] == []


@pytest.mark.django_db
def test_doctor_cannot_edit_after_24h(client, completed_appt, doctor_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    # Push completed_at beyond 24h
    completed_appt.completed_at = timezone.now() - timedelta(hours=25)
    completed_appt.save(update_fields=["completed_at"])

    res = client.patch(f"/api/v1/doctor/prescriptions/{rx_id}", PAYLOAD,
                       content_type="application/json")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "edit_window_closed"


@pytest.mark.django_db
def test_doctor_cannot_edit_other_doctors_prescription(client, completed_appt, doctor_user, doctor2_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    client_login(client, doctor2_user)
    res = client.patch(f"/api/v1/doctor/prescriptions/{rx_id}", PAYLOAD,
                       content_type="application/json")
    assert res.status_code == 404


@pytest.mark.django_db
def test_patient_reads_own_prescription(client, completed_appt, doctor_user, patient_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    client_login(client, patient_user)
    list_res = client.get("/api/v1/patient/prescriptions")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    detail_res = client.get(f"/api/v1/patient/prescriptions/{rx_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["diagnosis"] == "Acute bronchitis"
    assert len(detail_res.json()["medicines"]) == 1


@pytest.mark.django_db
def test_patient_cannot_read_other_patients_prescription(client, completed_appt, doctor_user, patient2_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    client_login(client, patient2_user)
    res = client.get(f"/api/v1/patient/prescriptions/{rx_id}")
    assert res.status_code == 404


@pytest.mark.django_db
def test_patient_cannot_patch_prescription(client, completed_appt, doctor_user, patient_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    client_login(client, patient_user)
    res = client.patch(f"/api/v1/doctor/prescriptions/{rx_id}", PAYLOAD,
                       content_type="application/json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_pdf_generation_returns_bytes(client, completed_appt, doctor_user, patient_user):
    client_login(client, doctor_user)
    create_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/prescription",
                              PAYLOAD, content_type="application/json")
    rx_id = create_res.json()["id"]

    client_login(client, patient_user)
    res = client.get(f"/api/v1/patient/prescriptions/{rx_id}/pdf")
    assert res.status_code == 200
    assert res["Content-Type"] == "application/pdf"
    assert len(res.content) > 100  # PDF has actual content
