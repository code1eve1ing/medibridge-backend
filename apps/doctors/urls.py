from django.urls import path
from . import views

doctor_patterns = [
    path("profile", views.doctor_profile, name="doctor-profile"),
    path("education", views.doctor_education_list, name="doctor-education-list"),
    path("education/<int:pk>", views.doctor_education_detail, name="doctor-education-detail"),
    path("slots", views.doctor_slots_list, name="doctor-slots-list"),
    path("slots/<int:pk>", views.doctor_slot_detail, name="doctor-slot-detail"),
]

admin_patterns = [
    path("doctors/invite", views.admin_doctor_invite, name="admin-doctors-invite"),
    path("doctors/<int:pk>/verify", views.admin_doctor_verify, name="admin-doctors-verify"),
    path("doctors", views.admin_doctor_list, name="admin-doctors"),
]

public_patterns = [
    path("specializations", views.public_specializations, name="public-specializations"),
    path("doctors/<slug:slug>", views.public_doctor_detail, name="public-doctor-detail"),
    path("doctors", views.public_doctor_list, name="public-doctors"),
]

patient_patterns = [
    path("doctors/<int:doctor_id>/available-slots", views.patient_available_slots, name="patient-available-slots"),
]
