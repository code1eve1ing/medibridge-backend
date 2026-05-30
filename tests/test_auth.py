import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.accounts.models import User, EmailVerificationToken, PasswordResetToken


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def verified_patient(db):
    user = User.objects.create_user(email="patient@test.com", password="Testpass123!", role="patient")
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def unverified_patient(db):
    return User.objects.create_user(email="unverified@test.com", password="Testpass123!", role="patient")


# --- Signup ---

@pytest.mark.django_db
def test_signup_creates_user_and_sends_email(client, mailoutbox):
    res = client.post("/api/v1/auth/signup/patient", {"email": "new@test.com", "password": "Testpass123!"}, format="json")
    assert res.status_code == 201
    assert User.objects.filter(email="new@test.com").exists()
    assert EmailVerificationToken.objects.filter(user__email="new@test.com").exists()


@pytest.mark.django_db
def test_signup_duplicate_email_rejected(client, verified_patient):
    res = client.post("/api/v1/auth/signup/patient", {"email": "patient@test.com", "password": "Testpass123!"}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_weak_password_rejected(client):
    res = client.post("/api/v1/auth/signup/patient", {"email": "x@test.com", "password": "short"}, format="json")
    assert res.status_code == 400


# --- Login ---

@pytest.mark.django_db
def test_login_verified_user_sets_cookies(client, verified_patient):
    res = client.post("/api/v1/auth/login", {"email": "patient@test.com", "password": "Testpass123!"}, format="json")
    assert res.status_code == 200
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies
    assert res.json()["user"]["email"] == "patient@test.com"


@pytest.mark.django_db
def test_login_unverified_user_returns_403(client, unverified_patient):
    res = client.post("/api/v1/auth/login", {"email": "unverified@test.com", "password": "Testpass123!"}, format="json")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "email_not_verified"


@pytest.mark.django_db
def test_login_wrong_password_returns_401(client, verified_patient):
    res = client.post("/api/v1/auth/login", {"email": "patient@test.com", "password": "wrongpass"}, format="json")
    assert res.status_code == 401


# --- Me ---

@pytest.mark.django_db
def test_me_returns_401_without_cookie(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.django_db
def test_me_returns_user_with_valid_cookie(client, verified_patient):
    login_res = client.post("/api/v1/auth/login", {"email": "patient@test.com", "password": "Testpass123!"}, format="json")
    client.cookies = login_res.cookies
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "patient@test.com"


# --- Logout ---

@pytest.mark.django_db
def test_logout_clears_cookies(client, verified_patient):
    login_res = client.post("/api/v1/auth/login", {"email": "patient@test.com", "password": "Testpass123!"}, format="json")
    client.cookies = login_res.cookies
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    # After logout, me should return 401
    res2 = client.get("/api/v1/auth/me")
    assert res2.status_code == 401


# --- Email Verification ---

@pytest.mark.django_db
def test_verify_email_marks_user_verified(client, unverified_patient):
    token_obj = EmailVerificationToken.objects.create(user=unverified_patient)
    res = client.post("/api/v1/auth/verify-email", {"token": token_obj.token}, format="json")
    assert res.status_code == 200
    unverified_patient.refresh_from_db()
    assert unverified_patient.is_email_verified is True


@pytest.mark.django_db
def test_verify_email_expired_token_rejected(client, unverified_patient):
    token_obj = EmailVerificationToken.objects.create(user=unverified_patient)
    token_obj.expires_at = timezone.now() - timedelta(hours=1)
    token_obj.save()
    res = client.post("/api/v1/auth/verify-email", {"token": token_obj.token}, format="json")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "token_expired"


@pytest.mark.django_db
def test_verify_email_invalid_token_rejected(client):
    res = client.post("/api/v1/auth/verify-email", {"token": "doesnotexist"}, format="json")
    assert res.status_code == 400


# --- Password Reset ---

@pytest.mark.django_db
def test_reset_password_flow(client, verified_patient):
    token_obj = PasswordResetToken.objects.create(user=verified_patient)
    res = client.post("/api/v1/auth/reset-password", {"token": token_obj.token, "new_password": "NewSecure456!"}, format="json")
    assert res.status_code == 200
    verified_patient.refresh_from_db()
    assert verified_patient.check_password("NewSecure456!")


@pytest.mark.django_db
def test_reset_password_old_password_rejected_after_reset(client, verified_patient):
    token_obj = PasswordResetToken.objects.create(user=verified_patient)
    client.post("/api/v1/auth/reset-password", {"token": token_obj.token, "new_password": "NewSecure456!"}, format="json")
    res = client.post("/api/v1/auth/login", {"email": "patient@test.com", "password": "Testpass123!"}, format="json")
    assert res.status_code == 401


@pytest.mark.django_db
def test_reset_password_expired_token_rejected(client, verified_patient):
    token_obj = PasswordResetToken.objects.create(user=verified_patient)
    token_obj.expires_at = timezone.now() - timedelta(minutes=1)
    token_obj.save()
    res = client.post("/api/v1/auth/reset-password", {"token": token_obj.token, "new_password": "NewSecure456!"}, format="json")
    assert res.status_code == 400
