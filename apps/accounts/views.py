from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.notifications.services import send_email
from .models import EmailVerificationToken, PasswordResetToken, User
from .serializers import (
    DoctorSignupSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    PatientSignupSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class LoginRateThrottle(AnonRateThrottle):
    rate = "5/min"
    scope = "login"


class PasswordResetRateThrottle(AnonRateThrottle):
    rate = "3/min"
    scope = "password_reset"


def _set_jwt_cookies(response, refresh):
    access = refresh.access_token
    jwt_settings = settings.SIMPLE_JWT

    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE"],
        value=str(access),
        max_age=int(jwt_settings["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
        path="/",
    )
    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE_REFRESH"],
        value=str(refresh),
        max_age=int(jwt_settings["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
        path="/api/v1/auth/",
    )
    return response


def _clear_jwt_cookies(response):
    jwt_settings = settings.SIMPLE_JWT
    response.delete_cookie(jwt_settings["AUTH_COOKIE"])
    response.delete_cookie(jwt_settings["AUTH_COOKIE_REFRESH"], path="/api/v1/auth/")
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def signup_patient(request):
    serializer = PatientSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    if settings.DEBUG:
        # Auto-verify in dev so signups work without a real email inbox.
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return Response(
            {"message": "Account created. You can log in immediately (dev mode — email auto-verified)."},
            status=status.HTTP_201_CREATED,
        )

    token_obj = EmailVerificationToken.objects.create(user=user)
    verify_url = f"{settings.SITE_FRONTEND_URL}/auth/verify-email/{token_obj.token}"
    send_email(
        to_email=user.email,
        subject="Verify your MediBridge account",
        template_name="verification",
        context={"user": user, "verify_url": verify_url},
        context_type="user",
        context_id=user.id,
    )

    return Response(
        {"message": "Account created. Please check your email to verify your account."},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def signup_doctor(request):
    serializer = DoctorSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    if settings.DEBUG:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return Response(
            {"message": "Doctor account created. You can log in immediately (dev mode — email auto-verified)."},
            status=status.HTTP_201_CREATED,
        )

    token_obj = EmailVerificationToken.objects.create(user=user)
    verify_url = f"{settings.SITE_FRONTEND_URL}/auth/verify-email/{token_obj.token}"
    send_email(
        to_email=user.email,
        subject="Verify your MediBridge doctor account",
        template_name="verification",
        context={"user": user, "verify_url": verify_url},
        context_type="user",
        context_id=user.id,
    )

    return Response(
        {"message": "Doctor account created. Please verify your email before logging in."},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        request,
        username=serializer.validated_data["email"],
        password=serializer.validated_data["password"],
    )

    if user is None:
        return Response(
            {"error": {"code": "invalid_credentials", "message": "Invalid email or password."}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_email_verified:
        return Response(
            {"error": {"code": "email_not_verified", "message": "Please verify your email before logging in."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    refresh = RefreshToken.for_user(user)
    response = Response({"user": UserSerializer(user).data})
    return _set_jwt_cookies(response, refresh)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

    response = Response({"message": "Logged out successfully."})
    return _clear_jwt_cookies(response)


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
    if not refresh_token:
        return Response(
            {"error": {"code": "no_refresh_token", "message": "No refresh token provided."}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        old_token = RefreshToken(refresh_token)
        old_token.blacklist()
        new_refresh = RefreshToken.for_user(
            User.objects.get(id=old_token["user_id"])
        )
        response = Response({"message": "Token refreshed."})
        return _set_jwt_cookies(response, new_refresh)
    except (TokenError, User.DoesNotExist):
        response = Response(
            {"error": {"code": "invalid_refresh_token", "message": "Refresh token is invalid or expired."}},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        return _clear_jwt_cookies(response)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"user": UserSerializer(request.user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    serializer = VerifyEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        token_obj = EmailVerificationToken.objects.select_related("user").get(
            token=serializer.validated_data["token"]
        )
    except EmailVerificationToken.DoesNotExist:
        return Response(
            {"error": {"code": "invalid_token", "message": "Invalid verification token."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not token_obj.is_valid():
        return Response(
            {"error": {"code": "token_expired", "message": "This verification link has expired."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token_obj.used_at = timezone.now()
    token_obj.save()
    token_obj.user.is_email_verified = True
    token_obj.user.save()

    return Response({"message": "Email verified successfully. You can now log in."})


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification(request):
    serializer = ResendVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = User.objects.get(email=serializer.validated_data["email"])
    except User.DoesNotExist:
        return Response({"message": "If that email is registered, a new verification link has been sent."})

    if user.is_email_verified:
        return Response({"message": "This account is already verified."})

    token_obj = EmailVerificationToken.objects.create(user=user)
    verify_url = f"{settings.SITE_FRONTEND_URL}/auth/verify-email/{token_obj.token}"
    send_email(
        to_email=user.email,
        subject="Verify your MediBridge account",
        template_name="verification",
        context={"user": user, "verify_url": verify_url},
        context_type="user",
        context_id=user.id,
    )

    return Response({"message": "If that email is registered, a new verification link has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = User.objects.get(email=serializer.validated_data["email"])
        token_obj = PasswordResetToken.objects.create(user=user)
        reset_url = f"{settings.SITE_FRONTEND_URL}/auth/reset-password/{token_obj.token}"
        send_email(
            to_email=user.email,
            subject="Reset your MediBridge password",
            template_name="password_reset",
            context={"user": user, "reset_url": reset_url},
            context_type="user",
            context_id=user.id,
        )
    except User.DoesNotExist:
        pass

    return Response({"message": "If that email is registered, a password reset link has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        token_obj = PasswordResetToken.objects.select_related("user").get(
            token=serializer.validated_data["token"]
        )
    except PasswordResetToken.DoesNotExist:
        return Response(
            {"error": {"code": "invalid_token", "message": "Invalid or expired reset token."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not token_obj.is_valid():
        return Response(
            {"error": {"code": "token_expired", "message": "This reset link has expired."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token_obj.used_at = timezone.now()
    token_obj.save()
    token_obj.user.set_password(serializer.validated_data["new_password"])
    token_obj.user.save()

    return Response({"message": "Password reset successfully. You can now log in."})
