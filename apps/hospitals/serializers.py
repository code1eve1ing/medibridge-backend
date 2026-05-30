from rest_framework import serializers
from .models import Hospital, SurgeryPackage


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            "id", "name", "slug", "city", "state", "country",
            "description", "image", "accreditations", "website",
            "is_partner", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class SurgeryPackageSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    hospital_city = serializers.CharField(source="hospital.city", read_only=True)

    class Meta:
        model = SurgeryPackage
        fields = [
            "id", "hospital", "hospital_name", "hospital_city", "name", "slug",
            "surgery_type", "description",
            "total_duration_days", "hospital_stay_days", "recovery_stay_days",
            "price_usd",
            "includes_flight", "flight_class",
            "includes_visa_assistance",
            "includes_accommodation", "accommodation_type",
            "includes_transport", "includes_meals",
            "inclusions_text", "exclusions_text",
            "image", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "hospital_name", "hospital_city", "created_at", "updated_at"]
