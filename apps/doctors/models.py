import re
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to="doctor_photos/", null=True, blank=True)
    signature_image = models.ImageField(upload_to="doctor_signatures/", null=True, blank=True)
    bio = models.TextField(blank=True)
    medical_council_reg_no = models.CharField(max_length=100, unique=True, null=True, blank=True)
    years_of_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    consultation_fee_usd = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    consultation_duration_min = models.PositiveSmallIntegerField(default=30)
    languages = models.CharField(max_length=255, blank=True)
    hospital_affiliation = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    specializations = models.ManyToManyField(Specialization, blank=True, related_name="doctors")
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = re.sub(r"[^a-z0-9]+", "-", f"{self.first_name} {self.last_name}".strip().lower())
            base = base.strip("-") or "doctor"
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    @property
    def is_profile_complete(self):
        return all([
            self.first_name,
            self.last_name,
            self.phone,
            self.medical_council_reg_no,
            self.years_of_experience is not None,
            self.consultation_fee_usd is not None,
        ])


class DoctorEducation(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="education")
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=255)
    year_completed = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.degree} — {self.institution} ({self.year_completed})"


class DoctorAvailabilitySlot(models.Model):
    SLOT_TYPE_CHOICES = [
        ("recurring_weekly", "Recurring Weekly"),
        ("specific_date", "Specific Date"),
    ]
    DAY_CHOICES = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="slots")
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPE_CHOICES)
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES, null=True, blank=True)
    specific_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["doctor", "day_of_week", "is_active"]),
            models.Index(fields=["doctor", "specific_date", "is_active"]),
        ]

    def __str__(self):
        if self.slot_type == "recurring_weekly":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day = days[self.day_of_week] if self.day_of_week is not None else "?"
            return f"{day} {self.start_time}–{self.end_time}"
        return f"{self.specific_date} {self.start_time}–{self.end_time}"


class DoctorInvite(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_invites"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Invite for {self.email}"

    def is_valid(self):
        if self.accepted_at is not None:
            return False
        return timezone.now() <= self.expires_at

    @classmethod
    def create_for_email(cls, email, invited_by):
        return cls.objects.create(
            email=email,
            token=secrets.token_hex(32),
            invited_by=invited_by,
            expires_at=timezone.now() + timedelta(days=7),
        )
