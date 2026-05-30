import secrets
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.doctors.models import DoctorInvite, DoctorProfile, DoctorEducation


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(email="admin@test.com", password="Adminpass123!", role="admin")
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(email="doc@test.com", password="Testpass123!", role="doctor")
    user.is_email_verified = True
    user.save()
    DoctorProfile.objects.create(user=user, first_name="Jane", last_name="Doe")
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


def make_invite(admin_user, email="newdoc@test.local", expired=False, used=False):
    expires_at = timezone.now() + timedelta(days=7)
    if expired:
        expires_at = timezone.now() - timedelta(days=1)
    invite = DoctorInvite.objects.create(
        email=email,
        token=secrets.token_hex(32),
        invited_by=admin_user,
        expires_at=expires_at,
    )
    if used:
        invite.accepted_at = timezone.now()
        invite.save()
    return invite


# --- Invite ---

@pytest.mark.django_db
def test_admin_invite_doctor_returns_201(client, admin_user):
    login(client, admin_user, password="Adminpass123!")
    res = client.post("/api/v1/admin/doctors/invite", {"email": "newdoc@test.local"}, format="json")
    assert res.status_code == 201
    assert DoctorInvite.objects.filter(email="newdoc@test.local").exists()


@pytest.mark.django_db
def test_invite_requires_admin(client, patient_user):
    login(client, patient_user)
    res = client.post("/api/v1/admin/doctors/invite", {"email": "newdoc@test.local"}, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_doctor_cannot_invite(client, doctor_user):
    login(client, doctor_user)
    res = client.post("/api/v1/admin/doctors/invite", {"email": "newdoc@test.local"}, format="json")
    assert res.status_code == 403


# --- Doctor signup ---

@pytest.mark.django_db
def test_signup_doctor_valid_token(client, admin_user, db):
    invite = make_invite(admin_user)
    res = client.post("/api/v1/auth/signup/doctor", {
        "invite_token": invite.token,
        "email": invite.email,
        "password": "Strongpass123!",
        "first_name": "James",
        "last_name": "Smith",
    }, format="json")
    assert res.status_code == 201
    assert User.objects.filter(email=invite.email, role="doctor").exists()
    assert DoctorProfile.objects.filter(user__email=invite.email).exists()
    invite.refresh_from_db()
    assert invite.accepted_at is not None


@pytest.mark.django_db
def test_signup_doctor_used_token_rejected(client, admin_user, db):
    invite = make_invite(admin_user, used=True)
    res = client.post("/api/v1/auth/signup/doctor", {
        "invite_token": invite.token,
        "email": invite.email,
        "password": "Strongpass123!",
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_doctor_expired_token_rejected(client, admin_user, db):
    invite = make_invite(admin_user, expired=True)
    res = client.post("/api/v1/auth/signup/doctor", {
        "invite_token": invite.token,
        "email": invite.email,
        "password": "Strongpass123!",
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_doctor_email_mismatch_rejected(client, admin_user, db):
    invite = make_invite(admin_user, email="correct@test.local")
    res = client.post("/api/v1/auth/signup/doctor", {
        "invite_token": invite.token,
        "email": "wrong@test.local",
        "password": "Strongpass123!",
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_doctor_invalid_token_rejected(client, db):
    res = client.post("/api/v1/auth/signup/doctor", {
        "invite_token": "nonexistent" * 5,
        "email": "someone@test.local",
        "password": "Strongpass123!",
    }, format="json")
    assert res.status_code == 400


# --- Admin doctor list and verify ---

@pytest.mark.django_db
def test_admin_list_doctors(client, admin_user, doctor_user):
    login(client, admin_user, password="Adminpass123!")
    res = client.get("/api/v1/admin/doctors")
    assert res.status_code == 200
    emails = [d["email"] for d in res.json()]
    assert doctor_user.email in emails


@pytest.mark.django_db
def test_admin_verify_doctor(client, admin_user, doctor_user):
    login(client, admin_user, password="Adminpass123!")
    profile = doctor_user.doctor_profile
    res = client.post(f"/api/v1/admin/doctors/{profile.id}/verify")
    assert res.status_code == 200
    profile.refresh_from_db()
    assert profile.is_verified is True


@pytest.mark.django_db
def test_admin_verify_creates_audit_log(client, admin_user, doctor_user):
    from apps.core.models import AuditLog
    login(client, admin_user, password="Adminpass123!")
    profile = doctor_user.doctor_profile
    client.post(f"/api/v1/admin/doctors/{profile.id}/verify")
    assert AuditLog.objects.filter(action="doctor.verified", target_id=profile.id).exists()


# --- Doctor profile and education ---

@pytest.mark.django_db
def test_doctor_profile_get(client, doctor_user):
    login(client, doctor_user)
    res = client.get("/api/v1/doctor/profile")
    assert res.status_code == 200
    assert res.json()["first_name"] == "Jane"


@pytest.mark.django_db
def test_doctor_profile_patch(client, doctor_user):
    login(client, doctor_user)
    res = client.patch("/api/v1/doctor/profile", {"bio": "Expert in cardiology."}, format="json")
    assert res.status_code == 200
    assert res.json()["bio"] == "Expert in cardiology."


@pytest.mark.django_db
def test_doctor_cannot_set_is_verified(client, doctor_user):
    login(client, doctor_user)
    res = client.patch("/api/v1/doctor/profile", {"is_verified": True}, format="json")
    assert res.status_code == 200
    doctor_user.doctor_profile.refresh_from_db()
    assert doctor_user.doctor_profile.is_verified is False


@pytest.mark.django_db
def test_patient_cannot_access_doctor_profile(client, patient_user):
    login(client, patient_user)
    res = client.get("/api/v1/doctor/profile")
    assert res.status_code == 403


@pytest.mark.django_db
def test_doctor_education_crud(client, doctor_user):
    login(client, doctor_user)

    res = client.post("/api/v1/doctor/education", {
        "degree": "MBBS",
        "institution": "AIIMS Delhi",
        "year_completed": 2010,
    }, format="json")
    assert res.status_code == 201
    edu_id = res.json()["id"]

    res = client.get("/api/v1/doctor/education")
    assert res.status_code == 200
    assert any(e["id"] == edu_id for e in res.json())

    res = client.patch(f"/api/v1/doctor/education/{edu_id}", {"year_completed": 2011}, format="json")
    assert res.status_code == 200
    assert res.json()["year_completed"] == 2011

    res = client.delete(f"/api/v1/doctor/education/{edu_id}")
    assert res.status_code == 204
    assert not DoctorEducation.objects.filter(id=edu_id).exists()


@pytest.mark.django_db
def test_doctor_education_isolation(client, admin_user, doctor_user, db):
    other = User.objects.create_user(email="other_doc@test.com", password="Testpass123!", role="doctor")
    other.is_email_verified = True
    other.save()
    other_profile = DoctorProfile.objects.create(user=other)
    edu = DoctorEducation.objects.create(doctor=other_profile, degree="MD", institution="CMC", year_completed=2015)

    login(client, doctor_user)
    res = client.patch(f"/api/v1/doctor/education/{edu.id}", {"year_completed": 2020}, format="json")
    assert res.status_code == 404
