from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "is_email_verified", "date_joined"]
        read_only_fields = fields


class PatientSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role="patient",
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class DoctorSignupSerializer(serializers.Serializer):
    invite_token = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=100, default="")
    last_name = serializers.CharField(max_length=100, default="")

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        from apps.doctors.models import DoctorInvite

        try:
            invite = DoctorInvite.objects.get(token=data["invite_token"])
        except DoctorInvite.DoesNotExist:
            raise serializers.ValidationError({"invite_token": "Invalid invite token."})

        if invite.accepted_at is not None:
            raise serializers.ValidationError({"invite_token": "This invite has already been used."})
        if not invite.is_valid():
            raise serializers.ValidationError({"invite_token": "This invite has expired."})
        if invite.email.lower() != data["email"].lower():
            raise serializers.ValidationError({"email": "Email does not match the invitation."})
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError({"email": "An account with this email already exists."})

        data["_invite"] = invite
        return data

    def create(self, validated_data):
        from apps.doctors.models import DoctorProfile

        invite = validated_data.pop("_invite")
        validated_data.pop("invite_token")
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role="doctor",
        )
        DoctorProfile.objects.create(user=user, first_name=first_name, last_name=last_name)

        invite.accepted_at = timezone.now()
        invite.save(update_fields=["accepted_at"])

        return user
