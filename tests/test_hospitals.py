"""Phase 9 — Hospitals and Surgery Packages tests."""
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(email="hosp_admin@test.local", password="pass",
                                    role="admin", is_email_verified=True)

@pytest.fixture
def patient_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(email="hosp_patient@test.local", password="pass",
                                    role="patient", is_email_verified=True)

@pytest.fixture
def hospital(db):
    from apps.hospitals.models import Hospital
    return Hospital.objects.create(
        name="Apollo Hospital Delhi",
        city="New Delhi", state="Delhi", country="India",
        description="Top-tier multi-specialty hospital.",
        accreditations="JCI,NABH",
    )

@pytest.fixture
def package(db, hospital):
    from apps.hospitals.models import SurgeryPackage
    return SurgeryPackage.objects.create(
        hospital=hospital,
        name="Knee Replacement Standard",
        surgery_type="knee_replacement",
        description="Complete knee replacement package.",
        total_duration_days=14,
        hospital_stay_days=5,
        recovery_stay_days=9,
        price_usd="3500.00",
        includes_flight=True,
        includes_accommodation=True,
        includes_transport=True,
    )

@pytest.fixture
def inactive_package(db, hospital):
    from apps.hospitals.models import SurgeryPackage
    return SurgeryPackage.objects.create(
        hospital=hospital,
        name="Cardiac Bypass Premium",
        surgery_type="cardiac_bypass",
        description="Premium cardiac package.",
        total_duration_days=21,
        hospital_stay_days=10,
        recovery_stay_days=11,
        price_usd="8000.00",
        is_active=False,
    )

def login(client, user):
    client.post("/api/v1/auth/login", {"email": user.email, "password": "pass"},
                content_type="application/json")

PACKAGE_PAYLOAD = {
    "name": "Hip Replacement Standard",
    "surgery_type": "hip_replacement",
    "description": "Full hip replacement package.",
    "total_duration_days": 12,
    "hospital_stay_days": 4,
    "recovery_stay_days": 8,
    "price_usd": "4000.00",
    "includes_flight": True,
    "includes_accommodation": True,
    "includes_transport": True,
}


# ── Hospital admin CRUD ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_admin_can_list_hospitals(client, admin_user, hospital):
    login(client, admin_user)
    res = client.get("/api/v1/admin/hospitals")
    assert res.status_code == 200
    assert any(h["name"] == hospital.name for h in res.json())


@pytest.mark.django_db
def test_admin_can_create_hospital(client, admin_user):
    login(client, admin_user)
    res = client.post("/api/v1/admin/hospitals", {
        "name": "Fortis Gurgaon",
        "city": "Gurgaon", "state": "Haryana", "country": "India",
        "description": "World-class hospital.",
    }, content_type="application/json")
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Fortis Gurgaon"
    assert data["slug"] == "fortis-gurgaon"


@pytest.mark.django_db
def test_admin_can_update_hospital(client, admin_user, hospital):
    login(client, admin_user)
    res = client.patch(f"/api/v1/admin/hospitals/{hospital.id}",
                       {"accreditations": "JCI,NABH,ISO"}, content_type="application/json")
    assert res.status_code == 200
    assert res.json()["accreditations"] == "JCI,NABH,ISO"


@pytest.mark.django_db
def test_admin_can_delete_hospital(client, admin_user, hospital):
    login(client, admin_user)
    res = client.delete(f"/api/v1/admin/hospitals/{hospital.id}")
    assert res.status_code == 204


@pytest.mark.django_db
def test_non_admin_cannot_create_hospital(client, patient_user):
    login(client, patient_user)
    res = client.post("/api/v1/admin/hospitals", {
        "name": "Fake Hospital", "city": "X", "state": "Y", "country": "India",
        "description": "Desc",
    }, content_type="application/json")
    assert res.status_code == 403


# ── Package admin CRUD ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_admin_can_create_package(client, admin_user, hospital):
    login(client, admin_user)
    payload = {**PACKAGE_PAYLOAD, "hospital": hospital.id}
    res = client.post("/api/v1/admin/packages", payload, content_type="application/json")
    assert res.status_code == 201
    data = res.json()
    assert data["surgery_type"] == "hip_replacement"
    assert data["slug"] == "hip-replacement-standard"
    assert data["hospital_name"] == hospital.name


@pytest.mark.django_db
def test_admin_can_update_package(client, admin_user, package):
    login(client, admin_user)
    res = client.patch(f"/api/v1/admin/packages/{package.id}",
                       {"price_usd": "3800.00"}, content_type="application/json")
    assert res.status_code == 200
    assert res.json()["price_usd"] == "3800.00"


@pytest.mark.django_db
def test_admin_can_delete_package(client, admin_user, package):
    login(client, admin_user)
    res = client.delete(f"/api/v1/admin/packages/{package.id}")
    assert res.status_code == 204


# ── Public endpoints ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_public_package_list_returns_active_only(client, package, inactive_package):
    res = client.get("/api/v1/public/packages")
    assert res.status_code == 200
    slugs = [p["slug"] for p in res.json()]
    assert package.slug in slugs
    assert inactive_package.slug not in slugs


@pytest.mark.django_db
def test_public_package_list_filter_by_surgery_type(client, package, hospital):
    from apps.hospitals.models import SurgeryPackage
    SurgeryPackage.objects.create(
        hospital=hospital, name="Cardiac Package", surgery_type="cardiac_bypass",
        description="Desc", total_duration_days=20, hospital_stay_days=8,
        recovery_stay_days=12, price_usd="9000.00",
    )
    res = client.get("/api/v1/public/packages?surgery_type=knee_replacement")
    assert res.status_code == 200
    assert all(p["surgery_type"] == "knee_replacement" for p in res.json())
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_public_package_detail(client, package):
    res = client.get(f"/api/v1/public/packages/{package.slug}")
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == package.slug
    assert "related_packages" in data


@pytest.mark.django_db
def test_public_package_detail_includes_related(client, package, hospital):
    from apps.hospitals.models import Hospital, SurgeryPackage
    h2 = Hospital.objects.create(name="Medanta", city="Gurgaon", state="Haryana",
                                  country="India", description="Desc")
    SurgeryPackage.objects.create(
        hospital=h2, name="Knee Replacement Deluxe", surgery_type="knee_replacement",
        description="Desc", total_duration_days=16, hospital_stay_days=6,
        recovery_stay_days=10, price_usd="5000.00",
    )
    res = client.get(f"/api/v1/public/packages/{package.slug}")
    data = res.json()
    assert len(data["related_packages"]) == 1
    assert data["related_packages"][0]["surgery_type"] == "knee_replacement"
    assert data["related_packages"][0]["id"] != package.id


@pytest.mark.django_db
def test_inactive_package_not_accessible_via_public_detail(client, inactive_package):
    res = client.get(f"/api/v1/public/packages/{inactive_package.slug}")
    assert res.status_code == 404


@pytest.mark.django_db
def test_slug_auto_generated_on_create(client, admin_user, hospital):
    login(client, admin_user)
    payload = {**PACKAGE_PAYLOAD, "hospital": hospital.id, "name": "Total Hip Arthroplasty"}
    res = client.post("/api/v1/admin/packages", payload, content_type="application/json")
    assert res.status_code == 201
    assert res.json()["slug"] == "total-hip-arthroplasty"


@pytest.mark.django_db
def test_duplicate_slug_gets_suffix(db, hospital):
    from apps.hospitals.models import SurgeryPackage
    p1 = SurgeryPackage.objects.create(
        hospital=hospital, name="Knee Surgery",
        surgery_type="knee_replacement", description="d",
        total_duration_days=10, hospital_stay_days=4, recovery_stay_days=6, price_usd="3000",
    )
    p2 = SurgeryPackage.objects.create(
        hospital=hospital, name="Knee Surgery",
        surgery_type="knee_replacement", description="d2",
        total_duration_days=12, hospital_stay_days=5, recovery_stay_days=7, price_usd="3200",
    )
    assert p1.slug == "knee-surgery"
    assert p2.slug == "knee-surgery-1"


@pytest.mark.django_db
def test_public_hospital_list(client, hospital):
    res = client.get("/api/v1/public/hospitals")
    assert res.status_code == 200
    assert any(h["name"] == hospital.name for h in res.json())
