from rest_framework import serializers

from apps.doctors.models import DoctorProfile
from apps.doctors.serializers import SpecializationSerializer
from .models import Appointment, Prescription, PrescriptionMedicine, PrescribedTest, SymptomIntake


class _DoctorMinimalSerializer(serializers.ModelSerializer):
    specializations = SpecializationSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "first_name", "last_name", "slug", "specializations"]


class PatientIntakeSerializer(serializers.ModelSerializer):
    preferred_doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.filter(is_verified=True, is_available=True),
        required=False,
        allow_null=True,
    )
    matched_doctor_detail = _DoctorMinimalSerializer(source="matched_doctor", read_only=True)

    class Meta:
        model = SymptomIntake
        fields = [
            "id",
            "chief_complaint",
            "symptoms",
            "duration",
            "severity",
            "existing_conditions_note",
            "preferred_doctor",
            "status",
            "matched_doctor_detail",
            "matched_at",
            "admin_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "status", "matched_doctor_detail",
            "matched_at", "admin_notes", "created_at", "updated_at",
        ]


class AdminIntakeSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    preferred_doctor_detail = _DoctorMinimalSerializer(source="preferred_doctor", read_only=True)
    matched_doctor_detail = _DoctorMinimalSerializer(source="matched_doctor", read_only=True)
    matched_by_email = serializers.SerializerMethodField()

    class Meta:
        model = SymptomIntake
        fields = [
            "id",
            "patient_name",
            "patient_email",
            "chief_complaint",
            "symptoms",
            "duration",
            "severity",
            "existing_conditions_note",
            "preferred_doctor_detail",
            "status",
            "matched_doctor_detail",
            "matched_by_email",
            "matched_at",
            "admin_notes",
            "created_at",
            "updated_at",
        ]

    def get_patient_name(self, obj):
        p = obj.patient
        name = f"{p.first_name} {p.last_name}".strip()
        return name or obj.patient.user.email

    def get_patient_email(self, obj):
        return obj.patient.user.email

    def get_matched_by_email(self, obj):
        return obj.matched_by.email if obj.matched_by else None


class AdminMatchSerializer(serializers.Serializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.filter(is_verified=True, is_available=True)
    )
    admin_notes = serializers.CharField(required=False, allow_blank=True, default="")


# ── Phase 6: Appointments ────────────────────────────────────────────────────

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="doctor.id", read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_slug = serializers.CharField(source="doctor.slug", read_only=True)
    doctor_fee = serializers.CharField(source="doctor.consultation_fee_usd", read_only=True)
    has_prescription = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "doctor_id", "doctor_name", "doctor_slug", "doctor_fee",
            "intake", "parent_appointment", "fee_waived",
            "scheduled_start", "scheduled_end",
            "status", "payment_ref", "meeting_link", "notes", "has_prescription",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "payment_ref", "meeting_link", "created_at", "updated_at"]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.first_name} {obj.doctor.last_name}"

    def get_has_prescription(self, obj):
        return hasattr(obj, "prescription")


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    has_prescription = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "patient_name", "patient_email",
            "intake", "parent_appointment", "fee_waived",
            "scheduled_start", "scheduled_end",
            "status", "meeting_link", "notes", "has_prescription",
            "created_at", "updated_at",
        ]
        read_only_fields = ["meeting_link"]

    def get_patient_name(self, obj):
        p = obj.patient
        return f"{p.first_name} {p.last_name}".strip() or obj.patient.user.email

    def get_patient_email(self, obj):
        return obj.patient.user.email

    def get_has_prescription(self, obj):
        return hasattr(obj, "prescription")


class AppointmentCreateSerializer(serializers.Serializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.filter(is_verified=True, is_available=True)
    )
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    intake_id = serializers.PrimaryKeyRelatedField(
        queryset=SymptomIntake.objects.filter(status="matched"),
        required=False, allow_null=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        if data["scheduled_end"] <= data["scheduled_start"]:
            raise serializers.ValidationError("End must be after start.")
        return data


class AppointmentStatusSerializer(serializers.Serializer):
    ALLOWED = ["in_progress", "completed", "no_show"]
    status = serializers.ChoiceField(choices=ALLOWED)


class FollowUpCreateSerializer(serializers.Serializer):
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    fee_waived = serializers.BooleanField(default=False)

    def validate(self, data):
        if data["scheduled_end"] <= data["scheduled_start"]:
            raise serializers.ValidationError("End must be after start.")
        return data


# ── Phase 7: Prescriptions ───────────────────────────────────────────────────

class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionMedicine
        fields = [
            "id", "medicine_name", "dosage",
            "morning", "afternoon", "evening", "night",
            "meal_timing", "duration_days", "instructions",
        ]
        read_only_fields = ["id"]


class PrescribedTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescribedTest
        fields = ["id", "test_name", "urgency", "instructions"]
        read_only_fields = ["id"]


class PrescriptionReadSerializer(serializers.ModelSerializer):
    medicines = PrescriptionMedicineSerializer(many=True, read_only=True)
    tests = PrescribedTestSerializer(many=True, read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_reg_no = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    appointment_id = serializers.IntegerField(source="appointment.id", read_only=True)
    appointment_date = serializers.DateTimeField(source="appointment.scheduled_start", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id", "appointment_id", "appointment_date", "doctor_name", "doctor_reg_no",
            "patient_name", "patient_email",
            "diagnosis", "general_notes",
            "follow_up_required", "follow_up_after_days",
            "medicines", "tests",
            "created_at", "updated_at",
        ]

    def get_doctor_name(self, obj):
        d = obj.appointment.doctor
        return f"Dr. {d.first_name} {d.last_name}"

    def get_doctor_reg_no(self, obj):
        return obj.appointment.doctor.medical_council_reg_no or ""

    def get_patient_name(self, obj):
        p = obj.appointment.patient
        return f"{p.first_name} {p.last_name}".strip() or p.user.email

    def get_patient_email(self, obj):
        return obj.appointment.patient.user.email


class PatientPrescriptionListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    appointment_date = serializers.DateTimeField(source="appointment.scheduled_start", read_only=True)
    appointment_id = serializers.IntegerField(source="appointment.id", read_only=True)

    class Meta:
        model = Prescription
        fields = ["id", "appointment_id", "appointment_date", "doctor_name", "diagnosis", "created_at"]

    def get_doctor_name(self, obj):
        d = obj.appointment.doctor
        return f"Dr. {d.first_name} {d.last_name}"


class PrescriptionWriteSerializer(serializers.ModelSerializer):
    medicines = PrescriptionMedicineSerializer(many=True, required=False)
    tests = PrescribedTestSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = [
            "diagnosis", "general_notes",
            "follow_up_required", "follow_up_after_days",
            "medicines", "tests",
        ]

    def create(self, validated_data):
        medicines_data = validated_data.pop("medicines", [])
        tests_data = validated_data.pop("tests", [])
        prescription = Prescription.objects.create(**validated_data)
        for m in medicines_data:
            PrescriptionMedicine.objects.create(prescription=prescription, **m)
        for t in tests_data:
            PrescribedTest.objects.create(prescription=prescription, **t)
        return prescription

    def update(self, instance, validated_data):
        medicines_data = validated_data.pop("medicines", [])
        tests_data = validated_data.pop("tests", [])
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        instance.medicines.all().delete()
        instance.tests.all().delete()
        for m in medicines_data:
            PrescriptionMedicine.objects.create(prescription=instance, **m)
        for t in tests_data:
            PrescribedTest.objects.create(prescription=instance, **t)
        return instance
