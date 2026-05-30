from django.db import models
from django.conf import settings


class PatientProfile(models.Model):
    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile"
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    alt_phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    address_line = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=64, default="America/Toronto")
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    existing_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="patient_photos/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.email})"

    @property
    def is_complete(self):
        required = [self.first_name, self.last_name, self.date_of_birth, self.gender, self.phone, self.country]
        return all(bool(f) for f in required)


class MedicalReport(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="medical_reports")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="medical_reports/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.patient.user.email} — {self.title}"
