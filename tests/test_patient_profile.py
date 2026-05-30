import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.patients.models import PatientProfile


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def patient(db):
    user = User.objects.create_user(email="patient@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def other_patient(db):
    user = User.objects.create_user(email="other@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


def login(client, user):
    res = client.post("/api/v1/auth/login", {"email": user.email, "password": "Testpass123!"}, format="json")
    client.cookies = res.cookies
    return client


# --- Signal ---

@pytest.mark.django_db
def test_profile_auto_created_on_patient_signup(db):
    user = User.objects.create_user(email="new@test.com", password="Testpass123!", role="patient")
    assert PatientProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_profile_not_created_for_non_patient(db):
    user = User.objects.create_user(email="doc@test.com", password="Testpass123!", role="doctor")
    assert not PatientProfile.objects.filter(user=user).exists()


# --- GET profile ---

@pytest.mark.django_db
def test_get_profile_returns_own_profile(client, patient):
    login(client, patient)
    res = client.get("/api/v1/patient/profile")
    assert res.status_code == 200
    assert res.json()["is_complete"] is False


@pytest.mark.django_db
def test_get_profile_unauthenticated_returns_401(client):
    res = client.get("/api/v1/patient/profile")
    assert res.status_code == 401


# --- PATCH profile ---

@pytest.mark.django_db
def test_patch_profile_updates_fields(client, patient):
    login(client, patient)
    res = client.patch(
        "/api/v1/patient/profile",
        {"first_name": "Alice", "last_name": "Smith", "phone": "+1-416-555-0100",
         "country": "Canada", "date_of_birth": "1990-05-15", "gender": "female"},
        format="json",
    )
    assert res.status_code == 200
    assert res.json()["first_name"] == "Alice"
    assert res.json()["is_complete"] is True


@pytest.mark.django_db
def test_patch_profile_future_dob_rejected(client, patient):
    login(client, patient)
    res = client.patch("/api/v1/patient/profile", {"date_of_birth": "2099-01-01"}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_patch_profile_persists_after_refetch(client, patient):
    login(client, patient)
    client.patch("/api/v1/patient/profile", {"first_name": "Bob"}, format="json")
    res = client.get("/api/v1/patient/profile")
    assert res.json()["first_name"] == "Bob"


@pytest.mark.django_db
def test_doctor_cannot_access_patient_profile_endpoint(client, db):
    doc = User.objects.create_user(email="doc@test.com", password="Testpass123!", role="doctor")
    doc.is_email_verified = True
    doc.save()
    login(client, doc)
    res = client.get("/api/v1/patient/profile")
    assert res.status_code == 403
