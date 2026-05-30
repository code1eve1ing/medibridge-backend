from rest_framework import serializers

from .models import PatientTravelInfo, RecommendationMessage, SurgeryPackageBooking, SurgeryCoupon, SurgeryRecommendation, TravelDocument


class TravelDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelDocument
        fields = ["id", "doc_type", "doc_number", "issue_date", "expiry_date",
                  "uploaded_at", "is_verified"]
        read_only_fields = ["id", "uploaded_at", "is_verified"]


class PatientTravelInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientTravelInfo
        exclude = ["id", "booking"]


class SurgeryCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgeryCoupon
        fields = ["code", "issued_at", "valid_from", "valid_until"]


class SurgeryBookingListSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)
    hospital_name = serializers.CharField(source="package.hospital.name", read_only=True)
    surgery_type = serializers.CharField(source="package.surgery_type", read_only=True)
    recommended_by_doctor = serializers.SerializerMethodField()

    class Meta:
        model = SurgeryPackageBooking
        fields = ["id", "package", "package_name", "hospital_name", "surgery_type",
                  "status", "tentative_date", "total_amount_usd", "created_at",
                  "recommended_by_doctor"]

    def get_recommended_by_doctor(self, obj):
        try:
            rec = SurgeryRecommendation.objects.select_related("doctor").get(
                patient=obj.patient, package=obj.package
            )
            return f"Dr. {rec.doctor.first_name} {rec.doctor.last_name}".strip()
        except SurgeryRecommendation.DoesNotExist:
            return None


class SurgeryBookingDetailSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)
    package_slug = serializers.CharField(source="package.slug", read_only=True)
    hospital_name = serializers.CharField(source="package.hospital.name", read_only=True)
    hospital_city = serializers.CharField(source="package.hospital.city", read_only=True)
    surgery_type = serializers.CharField(source="package.surgery_type", read_only=True)
    travel_info = PatientTravelInfoSerializer(read_only=True)
    documents = TravelDocumentSerializer(many=True, read_only=True)
    coupon = SurgeryCouponSerializer(read_only=True)
    recommendation = serializers.SerializerMethodField()

    class Meta:
        model = SurgeryPackageBooking
        fields = [
            "id", "package", "package_name", "package_slug", "hospital_name",
            "hospital_city", "surgery_type", "status", "tentative_date",
            "total_amount_usd", "payment_ref", "travel_info", "documents",
            "coupon", "recommendation", "created_at", "updated_at",
        ]

    def get_recommendation(self, obj):
        try:
            rec = SurgeryRecommendation.objects.select_related(
                "doctor", "appointment"
            ).get(patient=obj.patient, package=obj.package)
        except SurgeryRecommendation.DoesNotExist:
            return None

        result = {
            "id": rec.id,
            "doctor_name": f"Dr. {rec.doctor.first_name} {rec.doctor.last_name}".strip(),
            "notes": rec.notes,
            "appointment_id": rec.appointment_id,
            "appointment_date": rec.appointment.scheduled_start.isoformat() if rec.appointment else None,
        }
        if rec.appointment:
            try:
                rx = rec.appointment.prescription
                result["prescription"] = {
                    "id": rx.id,
                    "diagnosis": rx.diagnosis,
                    "general_notes": rx.general_notes,
                    "medicines": [
                        {
                            "medicine_name": m.medicine_name,
                            "dosage": m.dosage,
                            "duration_days": m.duration_days,
                            "morning": m.morning,
                            "afternoon": m.afternoon,
                            "evening": m.evening,
                            "night": m.night,
                            "meal_timing": m.meal_timing,
                        }
                        for m in rx.medicines.all()
                    ],
                    "tests": [{"test_name": t.test_name, "urgency": t.urgency} for t in rx.tests.all()],
                }
            except Exception:
                result["prescription"] = None
        return result


class SurgeryBookingCreateSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
    tentative_date = serializers.DateField()

    def validate_package_id(self, value):
        from apps.hospitals.models import SurgeryPackage
        try:
            pkg = SurgeryPackage.objects.get(pk=value, is_active=True)
        except SurgeryPackage.DoesNotExist:
            raise serializers.ValidationError("Package not found or inactive.")
        self.context["package"] = pkg
        return value


class TravelInfoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientTravelInfo
        exclude = ["id", "booking"]


class SurgeryRecommendationSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)
    package_slug = serializers.CharField(source="package.slug", read_only=True)
    hospital_name = serializers.CharField(source="package.hospital.name", read_only=True)
    surgery_type = serializers.CharField(source="package.surgery_type", read_only=True)
    price_usd = serializers.CharField(source="package.price_usd", read_only=True)
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    unread_for_doctor = serializers.SerializerMethodField()
    unread_for_patient = serializers.SerializerMethodField()

    class Meta:
        model = SurgeryRecommendation
        fields = [
            "id", "status", "admin_notes", "package", "package_name", "package_slug",
            "hospital_name", "surgery_type", "price_usd", "doctor_name", "patient_name",
            "patient_email", "notes", "appointment", "created_at",
            "unread_for_doctor", "unread_for_patient",
        ]

    def get_unread_for_doctor(self, obj):
        # Doctor only sees the doctor↔admin thread
        return obj.messages.filter(
            thread_type="doctor", sender_role="admin", read_by_doctor=False
        ).count()

    def get_unread_for_patient(self, obj):
        # Patient only sees the patient↔admin thread
        return obj.messages.filter(
            thread_type="patient", sender_role="admin", read_by_patient=False
        ).count()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.first_name} {obj.doctor.last_name}".strip()

    def get_patient_name(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return name or obj.patient.user.email

    def get_patient_email(self, obj):
        return obj.patient.user.email


class AdminSurgeryRecommendationSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    package_name = serializers.CharField(source="package.name", read_only=True)
    package_slug = serializers.CharField(source="package.slug", read_only=True)
    hospital_name = serializers.CharField(source="package.hospital.name", read_only=True)
    surgery_type = serializers.CharField(source="package.surgery_type", read_only=True)
    price_usd = serializers.CharField(source="package.price_usd", read_only=True)
    unread_for_admin_from_doctor = serializers.SerializerMethodField()
    unread_for_admin_from_patient = serializers.SerializerMethodField()

    class Meta:
        model = SurgeryRecommendation
        fields = [
            "id", "status", "admin_notes", "package", "package_name", "package_slug",
            "hospital_name", "surgery_type", "price_usd",
            "doctor_name", "patient_name", "patient_email",
            "notes", "appointment", "created_at",
            "unread_for_admin_from_doctor", "unread_for_admin_from_patient",
        ]

    def get_unread_for_admin_from_doctor(self, obj):
        return obj.messages.filter(
            thread_type="doctor", sender_role="doctor", read_by_admin=False
        ).count()

    def get_unread_for_admin_from_patient(self, obj):
        return obj.messages.filter(
            thread_type="patient", sender_role="patient", read_by_admin=False
        ).count()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.first_name} {obj.doctor.last_name}".strip()

    def get_patient_name(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return name or obj.patient.user.email

    def get_patient_email(self, obj):
        return obj.patient.user.email


class RecommendationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.SerializerMethodField()

    class Meta:
        model = RecommendationMessage
        fields = ["id", "sender_role", "sender_name", "sender_email", "body", "created_at"]
        read_only_fields = ["id", "sender_role", "sender_name", "sender_email", "created_at"]

    def get_sender_name(self, obj):
        if not obj.sender:
            return "Unknown"
        user = obj.sender
        if obj.sender_role == "doctor" and hasattr(user, "doctor_profile"):
            p = user.doctor_profile
            return f"Dr. {p.first_name} {p.last_name}".strip() or user.email
        if obj.sender_role == "patient" and hasattr(user, "patient_profile"):
            p = user.patient_profile
            return f"{p.first_name} {p.last_name}".strip() or user.email
        if obj.sender_role == "admin":
            return "Admin Team"
        return user.email

    def get_sender_email(self, obj):
        return obj.sender.email if obj.sender else ""


class RecommendationMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()


class SurgeryRecommendationCreateSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()
    package_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        from apps.consultations.models import Appointment
        from apps.hospitals.models import SurgeryPackage
        doctor = self.context["doctor"]

        try:
            appt = Appointment.objects.select_related("patient__user").get(
                pk=data["appointment_id"], doctor=doctor, status="completed"
            )
        except Appointment.DoesNotExist:
            raise serializers.ValidationError(
                {"appointment_id": "Completed appointment not found for this doctor."}
            )

        try:
            pkg = SurgeryPackage.objects.get(pk=data["package_id"], is_active=True)
        except SurgeryPackage.DoesNotExist:
            raise serializers.ValidationError(
                {"package_id": "Surgery package not found or inactive."}
            )

        data["appointment"] = appt
        data["package"] = pkg
        return data

    def create(self, validated_data):
        return SurgeryRecommendation.objects.create(
            doctor=self.context["doctor"],
            patient=validated_data["appointment"].patient,
            appointment=validated_data["appointment"],
            package=validated_data["package"],
            notes=validated_data.get("notes", ""),
        )
