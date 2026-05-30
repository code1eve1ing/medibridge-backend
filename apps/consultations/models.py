from django.conf import settings
from django.db import models


class SymptomIntake(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("matched", "Matched"),
        ("cancelled", "Cancelled"),
    ]
    SEVERITY_CHOICES = [
        ("mild", "Mild"),
        ("moderate", "Moderate"),
        ("severe", "Severe"),
    ]

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="symptom_intakes",
    )
    chief_complaint = models.TextField()
    symptoms = models.TextField()
    duration = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    existing_conditions_note = models.TextField(blank=True)
    preferred_doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_in_intakes",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    matched_doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matched_intakes",
    )
    matched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matched_intakes",
    )
    matched_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Intake({self.patient.user.email}, {self.status})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("proposed", "Proposed"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
    ]

    patient = models.ForeignKey(
        "patients.PatientProfile", on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        "doctors.DoctorProfile", on_delete=models.CASCADE, related_name="appointments"
    )
    intake = models.ForeignKey(
        SymptomIntake, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="appointments"
    )
    parent_appointment = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="follow_ups"
    )
    fee_waived = models.BooleanField(default=False)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled", db_index=True)
    payment_ref = models.CharField(max_length=64, blank=True)
    meeting_link = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_start"]
        indexes = [models.Index(fields=["doctor", "scheduled_start", "status"])]

    def __str__(self):
        return f"Appt({self.patient.user.email} w/ Dr.{self.doctor.last_name}, {self.scheduled_start:%Y-%m-%d})"


class Prescription(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="prescription"
    )
    diagnosis = models.TextField()
    general_notes = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_after_days = models.PositiveSmallIntegerField(null=True, blank=True)
    pdf_file = models.FileField(upload_to="prescriptions/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rx({self.appointment})"


class PrescriptionMedicine(models.Model):
    MEAL_TIMING_CHOICES = [
        ("before_meal", "Before Meal"),
        ("after_meal", "After Meal"),
        ("with_meal", "With Meal"),
        ("any", "Any"),
    ]
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="medicines"
    )
    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=50)
    morning = models.BooleanField(default=False)
    afternoon = models.BooleanField(default=False)
    evening = models.BooleanField(default=False)
    night = models.BooleanField(default=False)
    meal_timing = models.CharField(max_length=15, choices=MEAL_TIMING_CHOICES, default="any")
    duration_days = models.PositiveSmallIntegerField()
    instructions = models.TextField(blank=True)


class PrescribedTest(models.Model):
    URGENCY_CHOICES = [("routine", "Routine"), ("urgent", "Urgent")]
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="tests"
    )
    test_name = models.CharField(max_length=150)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="routine")
    instructions = models.TextField(blank=True)
