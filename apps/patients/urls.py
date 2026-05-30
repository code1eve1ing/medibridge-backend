from django.urls import path
from . import views

urlpatterns = [
    path("profile", views.patient_profile, name="patient-profile"),
    path("medical-reports", views.patient_medical_reports, name="patient-medical-reports"),
    path("medical-reports/<int:pk>", views.patient_medical_report_delete, name="patient-medical-report-delete"),
]
