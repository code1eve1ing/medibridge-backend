from rest_framework import serializers
from .models import DoctorAvailabilitySlot, DoctorEducation, DoctorProfile, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ["id", "name", "slug"]


class DoctorEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorEducation
        fields = ["id", "degree", "institution", "year_completed"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    specializations = SpecializationSerializer(many=True, read_only=True)
    specialization_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(),
        many=True,
        write_only=True,
        source="specializations",
        required=False,
    )
    education = DoctorEducationSerializer(many=True, read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "first_name", "last_name", "slug", "phone",
            "profile_image", "signature_image", "bio",
            "medical_council_reg_no", "years_of_experience",
            "consultation_fee_usd", "consultation_duration_min",
            "languages", "hospital_affiliation", "timezone",
            "specializations", "specialization_ids",
            "education", "is_verified", "is_available",
            "is_profile_complete", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_verified", "created_at", "updated_at", "is_profile_complete"]

    def validate_medical_council_reg_no(self, value):
        if not value:
            return value
        qs = DoctorProfile.objects.filter(medical_council_reg_no=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This registration number is already in use.")
        return value


class DoctorAvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailabilitySlot
        fields = ["id", "slot_type", "day_of_week", "specific_date", "start_time", "end_time", "is_active"]

    def validate(self, data):
        slot_type = data.get("slot_type") or (self.instance.slot_type if self.instance else None)
        if slot_type == "recurring_weekly" and data.get("day_of_week") is None and not self.instance:
            raise serializers.ValidationError({"day_of_week": "Required for recurring weekly slots."})
        if slot_type == "specific_date" and not data.get("specific_date") and not self.instance:
            raise serializers.ValidationError({"specific_date": "Required for specific date slots."})
        start = data.get("start_time") or (self.instance.start_time if self.instance else None)
        end = data.get("end_time") or (self.instance.end_time if self.instance else None)
        if start and end and start >= end:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return data


class PublicDoctorSerializer(serializers.ModelSerializer):
    specializations = SpecializationSerializer(many=True, read_only=True)
    education = DoctorEducationSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "first_name", "last_name", "slug", "bio",
            "years_of_experience", "consultation_fee_usd", "consultation_duration_min",
            "languages", "hospital_affiliation", "timezone",
            "specializations", "education", "profile_image", "is_available", "is_verified",
        ]


class AdminDoctorListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    specializations = SpecializationSerializer(many=True, read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "first_name", "last_name", "slug", "email",
            "specializations", "is_verified", "is_available",
            "is_profile_complete", "created_at",
        ]
