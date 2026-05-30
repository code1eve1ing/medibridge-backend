"""Phase 8 — Follow-up consultation tests."""
import pytest
from datetime import timedelta
from django.utils import timezone


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def patient_user(db):
    from apps.accounts.models import User
    u = User.objects.create_user(email="fu_patient@test.local", password="pass", role="patient",
                                  is_email_verified=True)
    return u

@pytest.fixture
def doctor_user(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="fu_doctor@test.local", password="pass", role="doctor",
                                  is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="Arjun", last_name="Sharma",
                                  is_verified=True, is_available=True)
    return u

@pytest.fixture
def doctor2_user(db):
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile
    u = User.objects.create_user(email="fu_doctor2@test.local", password="pass", role="doctor",
                                  is_email_verified=True)
    DoctorProfile.objects.create(user=u, first_name="Priya", last_name="Nair",
                                  is_verified=True, is_available=True)
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
        payment_ref="DUMMY-ORIG",
        meeting_link="https://meet.jit.si/orig",
    )

def login(client, user):
    client.post("/api/v1/auth/login", {"email": user.email, "password": "pass"},
                content_type="application/json")

def future_slot():
    now = timezone.now()
    start = now + timedelta(days=7)
    return start.isoformat(), (start + timedelta(minutes=30)).isoformat()


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_doctor_proposes_fee_waived_follow_up(client, completed_appt, doctor_user):
    login(client, doctor_user)
    start, end = future_slot()
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                      {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                      content_type="application/json")
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "proposed"
    assert data["parent_appointment"] == completed_appt.id
    assert data["fee_waived"] is True


@pytest.mark.django_db
def test_doctor_proposes_fee_paid_follow_up(client, completed_appt, doctor_user):
    login(client, doctor_user)
    start, end = future_slot()
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                      {"scheduled_start": start, "scheduled_end": end, "fee_waived": False},
                      content_type="application/json")
    assert res.status_code == 201
    assert res.json()["fee_waived"] is False
    assert res.json()["status"] == "proposed"


@pytest.mark.django_db
def test_follow_up_rejected_for_non_completed_appointment(client, completed_appt, doctor_user):
    from apps.consultations.models import Appointment
    completed_appt.status = "scheduled"
    completed_appt.save(update_fields=["status"])
    login(client, doctor_user)
    start, end = future_slot()
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                      {"scheduled_start": start, "scheduled_end": end},
                      content_type="application/json")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_status"


@pytest.mark.django_db
def test_only_original_doctor_can_propose(client, completed_appt, doctor2_user):
    login(client, doctor2_user)
    start, end = future_slot()
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                      {"scheduled_start": start, "scheduled_end": end},
                      content_type="application/json")
    assert res.status_code == 404


@pytest.mark.django_db
def test_patient_confirms_fee_waived_follow_up(client, completed_appt, doctor_user, patient_user):
    login(client, doctor_user)
    start, end = future_slot()
    fu_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                         {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                         content_type="application/json")
    fu_id = fu_res.json()["id"]

    login(client, patient_user)
    res = client.post(f"/api/v1/patient/appointments/{fu_id}/confirm")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "scheduled"
    assert data["payment_ref"] == ""  # fee waived — no payment ref


@pytest.mark.django_db
def test_patient_confirms_fee_paid_follow_up_gets_payment_ref(client, completed_appt, doctor_user, patient_user):
    login(client, doctor_user)
    start, end = future_slot()
    fu_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                         {"scheduled_start": start, "scheduled_end": end, "fee_waived": False},
                         content_type="application/json")
    fu_id = fu_res.json()["id"]

    login(client, patient_user)
    res = client.post(f"/api/v1/patient/appointments/{fu_id}/confirm")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "scheduled"
    assert data["payment_ref"].startswith("DUMMY-")


@pytest.mark.django_db
def test_patient_cannot_confirm_other_patients_follow_up(client, completed_appt, doctor_user, patient_user):
    from apps.accounts.models import User
    other = User.objects.create_user(email="other_fu@test.local", password="pass", role="patient",
                                      is_email_verified=True)
    login(client, doctor_user)
    start, end = future_slot()
    fu_res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                         {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                         content_type="application/json")
    fu_id = fu_res.json()["id"]

    login(client, other)
    res = client.post(f"/api/v1/patient/appointments/{fu_id}/confirm")
    assert res.status_code == 404


@pytest.mark.django_db
def test_patient_sees_proposed_follow_up_in_list(client, completed_appt, doctor_user, patient_user):
    login(client, doctor_user)
    start, end = future_slot()
    client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                content_type="application/json")

    login(client, patient_user)
    res = client.get("/api/v1/patient/appointments")
    assert res.status_code == 200
    proposed = [a for a in res.json() if a["status"] == "proposed"]
    assert len(proposed) == 1
    assert proposed[0]["parent_appointment"] == completed_appt.id


@pytest.mark.django_db
def test_follow_up_slot_conflict_rejected(client, completed_appt, doctor_user):
    login(client, doctor_user)
    start, end = future_slot()
    client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                content_type="application/json")
    # Same slot again
    res = client.post(f"/api/v1/doctor/appointments/{completed_appt.id}/follow-up",
                      {"scheduled_start": start, "scheduled_end": end, "fee_waived": True},
                      content_type="application/json")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "slot_taken"
