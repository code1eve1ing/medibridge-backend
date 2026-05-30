import secrets

from django.db import models


def _travel_doc_path(instance, filename):
    return f"travel_docs/booking_{instance.booking_id}/{filename}"


class SurgeryPackageBooking(models.Model):
    STATUS_CHOICES = [
        ("info_pending", "Info Pending"),
        ("payment_pending", "Payment Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="surgery_bookings",
    )
    package = models.ForeignKey(
        "hospitals.SurgeryPackage",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="info_pending", db_index=True)
    tentative_date = models.DateField()
    total_amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    payment_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} — {self.package.name}"


class PatientTravelInfo(models.Model):
    VISA_STATUS_CHOICES = [
        ("not_applied", "Not Applied"),
        ("applied", "Applied"),
        ("granted", "Granted"),
        ("not_required", "Not Required"),
    ]

    booking = models.OneToOneField(
        SurgeryPackageBooking,
        on_delete=models.CASCADE,
        related_name="travel_info",
    )
    passport_number = models.CharField(max_length=50)
    passport_country = models.CharField(max_length=80)
    passport_expiry = models.DateField()
    visa_required = models.BooleanField(default=False)
    visa_status = models.CharField(max_length=15, choices=VISA_STATUS_CHOICES, default="not_required")
    current_occupation = models.CharField(max_length=150)
    employer = models.CharField(max_length=200, blank=True)
    annual_income_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    companion_count = models.PositiveSmallIntegerField(default=0)
    companion_details = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)

    def __str__(self):
        return f"TravelInfo for Booking #{self.booking_id}"


class TravelDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ("passport", "Passport"),
        ("visa", "Visa"),
        ("govt_id", "Government ID"),
        ("other", "Other"),
    ]

    booking = models.ForeignKey(
        SurgeryPackageBooking,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(max_length=10, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to=_travel_doc_path)
    doc_number = models.CharField(max_length=80, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
    )

    def __str__(self):
        return f"{self.doc_type} for Booking #{self.booking_id}"


class SurgeryRecommendation(models.Model):
    STATUS_CHOICES = [
        ("pending_admin", "Pending Admin Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="surgery_recommendations",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="surgery_recommendations",
    )
    appointment = models.ForeignKey(
        "consultations.Appointment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="surgery_recommendations",
    )
    package = models.ForeignKey(
        "hospitals.SurgeryPackage",
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending_admin", db_index=True
    )
    admin_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SurgeryRec #{self.id} — {self.package.name}"


class RecommendationMessage(models.Model):
    SENDER_ROLE_CHOICES = [
        ("admin", "Admin"),
        ("doctor", "Doctor"),
        ("patient", "Patient"),
    ]
    THREAD_TYPE_CHOICES = [
        ("doctor", "Doctor Thread"),   # admin ↔ doctor
        ("patient", "Patient Thread"), # admin ↔ patient
    ]

    recommendation = models.ForeignKey(
        SurgeryRecommendation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    thread_type = models.CharField(
        max_length=10, choices=THREAD_TYPE_CHOICES, default="doctor", db_index=True,
        help_text="Which conversation this message belongs to (admin↔doctor or admin↔patient).",
    )
    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="recommendation_messages",
    )
    sender_role = models.CharField(max_length=10, choices=SENDER_ROLE_CHOICES)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_by_admin = models.BooleanField(default=False)
    read_by_doctor = models.BooleanField(default=False)
    read_by_patient = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg #{self.id} on Rec #{self.recommendation_id} [{self.thread_type}] by {self.sender_role}"


class SurgeryCoupon(models.Model):
    booking = models.OneToOneField(
        SurgeryPackageBooking,
        on_delete=models.CASCADE,
        related_name="coupon",
    )
    code = models.CharField(max_length=32, unique=True)
    qr_image = models.ImageField(upload_to="coupons/qr/", null=True, blank=True)
    voucher_pdf = models.FileField(upload_to="coupons/pdf/", null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateField()
    valid_until = models.DateField()

    def __str__(self):
        return f"Coupon {self.code} for Booking #{self.booking_id}"

    @classmethod
    def generate_code(cls):
        while True:
            code = secrets.token_urlsafe(24)[:32]
            if not cls.objects.filter(code=code).exists():
                return code
