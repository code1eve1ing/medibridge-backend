"""Phase 10 — Surgery booking flow tests."""
import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def patient_user(db):
    from apps.accounts.models import User
    from apps.patients.models import PatientProfile
    u = User.objects.create_user(email="surg_patient@test.local", password="pass",
                                 role="patient", is_email_verified=True)
    PatientProfile.objects.filter(user=u).update(first_name="Test", last_name="Patient")
    return u

@pytest.fixture
def patient2_user(db):
    from apps.accounts.models import User
    u = User.objects.create_user(email="surg_patient2@test.local", password="pass",
                                 role="patient", is_email_verified=True)
    return u

@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(email="surg_admin@test.local", password="pass",
                                    role="admin", is_email_verified=True)

@pytest.fixture
def hospital(db):
    from apps.hospitals.models import Hospital
    return Hospital.objects.create(
        name="Test Hospital", city="Mumbai", state="Maharashtra", country="India",
        description="A test hospital.",
    )

@pytest.fixture
def package(db, hospital):
    from apps.hospitals.models import SurgeryPackage
    return SurgeryPackage.objects.create(
        hospital=hospital, name="Knee Surgery", surgery_type="knee_replacement",
        description="Desc", total_duration_days=14, hospital_stay_days=5,
        recovery_stay_days=9, price_usd="3500.00", is_active=True,
    )

@pytest.fixture
def booking(db, patient_user, package):
    from apps.surgery.models import SurgeryPackageBooking
    return SurgeryPackageBooking.objects.create(
        patient=patient_user.patient_profile,
        package=package,
        tentative_date="2027-03-15",
        total_amount_usd=package.price_usd,
        status="info_pending",
    )

@pytest.fixture
def payment_pending_booking(db, patient_user, package):
    from apps.surgery.models import PatientTravelInfo, SurgeryPackageBooking
    b = SurgeryPackageBooking.objects.create(
        patient=patient_user.patient_profile, package=package,
        tentative_date="2027-04-01", total_amount_usd=package.price_usd,
        status="payment_pending",
    )
    PatientTravelInfo.objects.create(
        booking=b, passport_number="P1234567", passport_country="Canada",
        passport_expiry="2030-01-01", visa_required=False,
        visa_status="not_required", current_occupation="Engineer",
    )
    return b

TRAVEL_INFO_PAYLOAD = {
    "passport_number": "P9876543",
    "passport_country": "Canada",
    "passport_expiry": "2030-06-01",
    "visa_required": False,
    "visa_status": "not_required",
    "current_occupation": "Software Engineer",
    "employer": "Acme Corp",
    "annual_income_usd": "90000.00",
    "companion_count": 0,
    "companion_details": "",
    "dietary_requirements": "",
    "special_needs": "",
}

def login(client, user):
    client.post("/api/v1/auth/login", {"email": user.email, "password": "pass"},
                content_type="application/json")

def small_pdf():
    return SimpleUploadedFile("passport.pdf", b"%PDF-1.4 test content", content_type="application/pdf")

def small_jpeg():
    return SimpleUploadedFile("photo.jpg", b"\xff\xd8\xff" + b"\x00" * 100, content_type="image/jpeg")

def large_file():
    return SimpleUploadedFile("big.pdf", b"x" * (11 * 1024 * 1024), content_type="application/pdf")

def text_file():
    return SimpleUploadedFile("doc.txt", b"hello", content_type="text/plain")


# ── Create booking ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_can_create_booking(client, patient_user, package):
    login(client, patient_user)
    res = client.post("/api/v1/patient/surgery-bookings", {
        "package_id": package.id,
        "tentative_date": "2027-06-01",
    }, content_type="application/json")
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "info_pending"
    assert data["total_amount_usd"] == str(package.price_usd)


@pytest.mark.django_db
def test_inactive_package_rejected(client, patient_user, package):
    package.is_active = False
    package.save()
    login(client, patient_user)
    res = client.post("/api/v1/patient/surgery-bookings",
                      {"package_id": package.id, "tentative_date": "2027-06-01"},
                      content_type="application/json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_patient_can_list_own_bookings(client, patient_user, booking):
    login(client, patient_user)
    res = client.get("/api/v1/patient/surgery-bookings")
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_patient_cannot_see_other_patients_bookings(client, patient2_user, booking):
    login(client, patient2_user)
    res = client.get("/api/v1/patient/surgery-bookings")
    assert res.status_code == 200
    assert len(res.json()) == 0


# ── Travel info ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_travel_info_moves_booking_to_payment_pending(client, patient_user, booking):
    login(client, patient_user)
    res = client.put(f"/api/v1/patient/surgery-bookings/{booking.id}/travel-info",
                     TRAVEL_INFO_PAYLOAD, content_type="application/json")
    assert res.status_code == 200
    booking.refresh_from_db()
    assert booking.status == "payment_pending"


@pytest.mark.django_db
def test_travel_info_can_be_updated_in_payment_pending(client, patient_user, payment_pending_booking):
    login(client, patient_user)
    payload = {**TRAVEL_INFO_PAYLOAD, "current_occupation": "Doctor"}
    res = client.put(
        f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/travel-info",
        payload, content_type="application/json",
    )
    assert res.status_code == 200
    assert res.json()["current_occupation"] == "Doctor"
    payment_pending_booking.refresh_from_db()
    assert payment_pending_booking.status == "payment_pending"


@pytest.mark.django_db
def test_other_patient_cannot_update_travel_info(client, patient2_user, booking):
    login(client, patient2_user)
    res = client.put(f"/api/v1/patient/surgery-bookings/{booking.id}/travel-info",
                     TRAVEL_INFO_PAYLOAD, content_type="application/json")
    assert res.status_code == 404


# ── Document upload ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patient_can_upload_document(client, patient_user, booking):
    login(client, patient_user)
    res = client.post(
        f"/api/v1/patient/surgery-bookings/{booking.id}/documents",
        {"file": small_pdf(), "doc_type": "passport"},
        format="multipart",
    )
    assert res.status_code == 201
    assert res.json()["doc_type"] == "passport"


@pytest.mark.django_db
def test_file_too_large_rejected(client, patient_user, booking):
    login(client, patient_user)
    res = client.post(
        f"/api/v1/patient/surgery-bookings/{booking.id}/documents",
        {"file": large_file(), "doc_type": "passport"},
        format="multipart",
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "file_too_large"


@pytest.mark.django_db
def test_invalid_file_type_rejected(client, patient_user, booking):
    login(client, patient_user)
    res = client.post(
        f"/api/v1/patient/surgery-bookings/{booking.id}/documents",
        {"file": text_file(), "doc_type": "passport"},
        format="multipart",
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_file_type"


@pytest.mark.django_db
def test_patient_can_delete_document(client, patient_user, booking):
    login(client, patient_user)
    upload_res = client.post(
        f"/api/v1/patient/surgery-bookings/{booking.id}/documents",
        {"file": small_pdf(), "doc_type": "passport"},
        format="multipart",
    )
    doc_id = upload_res.json()["id"]
    del_res = client.delete(f"/api/v1/patient/surgery-bookings/{booking.id}/documents/{doc_id}")
    assert del_res.status_code == 204


# ── Document serving ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_document_not_accessible_by_other_patient(client, patient_user, patient2_user, booking):
    login(client, patient_user)
    upload_res = client.post(
        f"/api/v1/patient/surgery-bookings/{booking.id}/documents",
        {"file": small_pdf(), "doc_type": "passport"},
        format="multipart",
    )
    doc_id = upload_res.json()["id"]

    login(client, patient2_user)
    res = client.get(f"/api/v1/patient/surgery-bookings/{booking.id}/documents/{doc_id}/file")
    assert res.status_code in (403, 404)


# ── State machine: cannot skip steps ─────────────────────────────────────────

@pytest.mark.django_db
def test_cannot_confirm_from_info_pending(client, patient_user, booking):
    login(client, patient_user)
    res = client.post(f"/api/v1/patient/surgery-bookings/{booking.id}/confirm",
                      content_type="application/json")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_status"


# ── Confirm & Voucher ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_confirm_booking_generates_voucher(client, patient_user, payment_pending_booking):
    login(client, patient_user)
    res = client.post(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/confirm",
                      content_type="application/json")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["payment_ref"].startswith("DUMMY-")
    assert "coupon" in data
    assert data["coupon"]["code"]


@pytest.mark.django_db
def test_voucher_pdf_accessible_by_owner(client, patient_user, payment_pending_booking):
    login(client, patient_user)
    client.post(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/confirm",
                content_type="application/json")
    res = client.get(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/voucher")
    assert res.status_code == 200
    assert res["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_voucher_not_accessible_by_other_patient(client, patient_user, patient2_user, payment_pending_booking):
    login(client, patient_user)
    client.post(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/confirm",
                content_type="application/json")

    login(client, patient2_user)
    res = client.get(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/voucher")
    assert res.status_code in (403, 404)


@pytest.mark.django_db
def test_voucher_accessible_by_admin(client, admin_user, patient_user, payment_pending_booking):
    login(client, patient_user)
    client.post(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/confirm",
                content_type="application/json")

    login(client, admin_user)
    res = client.get(f"/api/v1/patient/surgery-bookings/{payment_pending_booking.id}/voucher")
    assert res.status_code == 200
