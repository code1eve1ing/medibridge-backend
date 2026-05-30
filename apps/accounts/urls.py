from django.urls import path
from . import views

urlpatterns = [
    path("signup/patient", views.signup_patient, name="signup-patient"),
    path("signup/doctor", views.signup_doctor, name="signup-doctor"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("refresh", views.refresh, name="token-refresh"),
    path("me", views.me, name="me"),
    path("verify-email", views.verify_email, name="verify-email"),
    path("resend-verification", views.resend_verification, name="resend-verification"),
    path("forgot-password", views.forgot_password, name="forgot-password"),
    path("reset-password", views.reset_password, name="reset-password"),
]
