from django.urls import path
from . import views

patient_patterns = [
    path("symptom-intakes", views.patient_intake_list, name="patient-intake-list"),
    path("symptom-intakes/<int:pk>/cancel", views.patient_intake_cancel, name="patient-intake-cancel"),
    path("appointments", views.patient_appointment_list, name="patient-appointment-list"),
    path("appointments/<int:pk>/cancel", views.patient_appointment_cancel, name="patient-appointment-cancel"),
    path("appointments/<int:pk>/confirm", views.patient_confirm_follow_up, name="patient-confirm-follow-up"),
    path("prescriptions", views.patient_prescription_list, name="patient-prescription-list"),
    path("prescriptions/<int:pk>", views.patient_prescription_detail, name="patient-prescription-detail"),
    path("prescriptions/<int:pk>/pdf", views.patient_prescription_pdf, name="patient-prescription-pdf"),
]

admin_patterns = [
    path("symptom-intakes", views.admin_intake_list, name="admin-intake-list"),
    path("symptom-intakes/<int:pk>/match", views.admin_intake_match, name="admin-intake-match"),
]

doctor_patterns = [
    path("appointments", views.doctor_appointment_list, name="doctor-appointment-list"),
    path("appointments/<int:pk>/status", views.doctor_appointment_status, name="doctor-appointment-status"),
    path("appointments/<int:pk>/prescription", views.doctor_prescription, name="doctor-prescription"),
    path("appointments/<int:pk>/follow-up", views.doctor_follow_up, name="doctor-follow-up"),
    path("appointments/<int:pk>/patient-profile", views.doctor_appointment_patient_profile, name="doctor-appointment-patient-profile"),
    path("prescriptions/<int:pk>", views.doctor_prescription_edit, name="doctor-prescription-edit"),
]

dev_patterns = [
    path("payment", views.dev_dummy_payment, name="dev-payment"),
]
