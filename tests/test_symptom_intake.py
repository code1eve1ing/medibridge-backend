import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consultations.models import SymptomIntake
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile


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
def admin_user(db):
    user = User.objects.create_user(email="admin@test.com", password="Testpass123!", role="admin")
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
        is_verified=True, is_available=True,
    )
    return user


def login(client, user, password="Testpass123!"):
    res = client.post("/api/v1/auth/login", {"email": user.email, "password": password}, format="json")
    client.cookies = res.cookies
    return client


INTAKE_PAYLOAD = {
    "chief_complaint": "Persistent headache",
    "symptoms": "Throbbing pain, nausea, sensitivity to light",
    "duration": "3 days",
    "severity": "moderate",
    "existing_conditions_note": "No known conditions",
}


# --- Patient submit ---

@pytest.mark.django_db
def test_patient_submit_intake(client, patient_user):
    login(client, patient_user)
    res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    assert res.status_code == 201
    assert res.json()["status"] == "pending"
    assert SymptomIntake.objects.filter(patient=patient_user.patient_profile).count() == 1


@pytest.mark.django_db
def test_patient_submit_intake_with_preferred_doctor(client, patient_user, doctor_user):
    login(client, patient_user)
    doctor_id = doctor_user.doctor_profile.id
    payload = {**INTAKE_PAYLOAD, "preferred_doctor": doctor_id}
    res = client.post("/api/v1/patient/symptom-intakes", payload, format="json")
    assert res.status_code == 201
    assert SymptomIntake.objects.get(patient=patient_user.patient_profile).preferred_doctor_id == doctor_id


@pytest.mark.django_db
def test_patient_submit_invalid_severity(client, patient_user):
    login(client, patient_user)
    payload = {**INTAKE_PAYLOAD, "severity": "extreme"}
    res = client.post("/api/v1/patient/symptom-intakes", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_doctor_cannot_submit_intake(client, doctor_user):
    login(client, doctor_user)
    res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_cannot_submit_intake(client, db):
    res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    assert res.status_code == 401  # unauthenticated → 401; wrong role → 403


# --- Patient list (isolation) ---

@pytest.mark.django_db
def test_patient_list_own_intakes(client, patient_user):
    login(client, patient_user)
    client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    res = client.get("/api/v1/patient/symptom-intakes")
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.django_db
def test_patient_cannot_see_other_patient_intakes(client, patient_user, patient_user2):
    # patient2 submits an intake
    login(client, patient_user2)
    client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")

    # patient1 lists — should see empty
    login(client, patient_user)
    res = client.get("/api/v1/patient/symptom-intakes")
    assert res.status_code == 200
    assert len(res.json()) == 0


# --- Cancel ---

@pytest.mark.django_db
def test_patient_cancel_pending_intake(client, patient_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]
    res = client.post(f"/api/v1/patient/symptom-intakes/{pk}/cancel")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


@pytest.mark.django_db
def test_patient_cannot_cancel_matched_intake(client, patient_user, admin_user, doctor_user):
    # Submit intake
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    # Admin matches
    login(client, admin_user)
    client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id},
        format="json",
    )

    # Patient tries to cancel — should fail
    login(client, patient_user)
    res = client.post(f"/api/v1/patient/symptom-intakes/{pk}/cancel")
    assert res.status_code == 400


@pytest.mark.django_db
def test_patient_cannot_cancel_another_patients_intake(client, patient_user, patient_user2):
    login(client, patient_user2)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    login(client, patient_user)
    res = client.post(f"/api/v1/patient/symptom-intakes/{pk}/cancel")
    assert res.status_code == 404


# --- Admin list ---

@pytest.mark.django_db
def test_admin_list_all_intakes(client, admin_user, patient_user, patient_user2):
    login(client, patient_user)
    client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    login(client, patient_user2)
    client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")

    login(client, admin_user)
    res = client.get("/api/v1/admin/symptom-intakes")
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.django_db
def test_admin_filter_intakes_by_status(client, admin_user, patient_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]
    client.post(f"/api/v1/patient/symptom-intakes/{pk}/cancel")

    login(client, admin_user)
    res_pending = client.get("/api/v1/admin/symptom-intakes?status=pending")
    res_cancelled = client.get("/api/v1/admin/symptom-intakes?status=cancelled")
    assert len(res_pending.json()) == 0
    assert len(res_cancelled.json()) == 1


@pytest.mark.django_db
def test_patient_cannot_access_admin_intake_list(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/admin/symptom-intakes")
    assert res.status_code == 403


# --- Admin match ---

@pytest.mark.django_db
def test_admin_match_intake(client, admin_user, patient_user, doctor_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    login(client, admin_user)
    res = client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id},
        format="json",
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "matched"
    assert data["matched_doctor_detail"]["id"] == doctor_user.doctor_profile.id
    assert data["matched_by_email"] == admin_user.email
    assert data["matched_at"] is not None


@pytest.mark.django_db
def test_admin_match_sets_audit_log(client, admin_user, patient_user, doctor_user):
    from apps.core.models import AuditLog
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    login(client, admin_user)
    client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id},
        format="json",
    )
    assert AuditLog.objects.filter(action="intake.matched", target_id=pk).exists()


@pytest.mark.django_db
def test_admin_cannot_match_cancelled_intake(client, admin_user, patient_user, doctor_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]
    client.post(f"/api/v1/patient/symptom-intakes/{pk}/cancel")

    login(client, admin_user)
    res = client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_admin_match_with_notes(client, admin_user, patient_user, doctor_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    login(client, admin_user)
    res = client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id, "admin_notes": "Priority case"},
        format="json",
    )
    assert res.status_code == 200
    assert res.json()["admin_notes"] == "Priority case"


@pytest.mark.django_db
def test_non_admin_cannot_match(client, patient_user, doctor_user):
    # Create intake as patient
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    # Try to match as patient
    res = client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": doctor_user.doctor_profile.id},
        format="json",
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_match_invalid_doctor_id(client, admin_user, patient_user):
    login(client, patient_user)
    create_res = client.post("/api/v1/patient/symptom-intakes", INTAKE_PAYLOAD, format="json")
    pk = create_res.json()["id"]

    login(client, admin_user)
    res = client.post(
        f"/api/v1/admin/symptom-intakes/{pk}/match",
        {"doctor_id": 99999},
        format="json",
    )
    assert res.status_code == 400
