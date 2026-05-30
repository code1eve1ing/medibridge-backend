from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),
]

admin_patterns = [
    path("dashboard", views.admin_dashboard),
    path("bookings", views.admin_bookings),
    path("audit-log", views.admin_audit_log),
    path("users", views.admin_list_users),
    path("users/<int:user_id>", views.admin_user_detail),
    path("users/<int:user_id>/set-password", views.admin_set_user_password),
]
