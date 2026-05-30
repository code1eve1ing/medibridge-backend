from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "role", "is_active", "is_email_verified", "date_joined")
    list_filter = ("role", "is_active", "is_email_verified")
    search_fields = ("email",)
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Info", {"fields": ("role", "is_email_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2", "role")}),
    )
