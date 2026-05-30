from rest_framework.permissions import BasePermission
from rest_framework import exceptions


class IsAuthenticated(BasePermission):
    """
    Custom IsAuthenticated permission that returns 401 instead of 403 for unauthenticated users.
    This allows the frontend to properly handle token refresh.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.AuthenticationFailed()
        return True


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "patient")


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "doctor")


class IsVerifiedDoctor(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == "doctor"):
            return False
        return getattr(request.user.doctor_profile, "is_verified", False)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")
