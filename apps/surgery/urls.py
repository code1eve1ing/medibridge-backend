from django.urls import path
from . import views

patient_patterns = [
    path("surgery-bookings", views.booking_list),
    path("surgery-bookings/<int:pk>", views.booking_detail),
    path("surgery-bookings/<int:pk>/travel-info", views.booking_travel_info),
    path("surgery-bookings/<int:pk>/documents", views.booking_documents),
    path("surgery-bookings/<int:pk>/documents/<int:did>", views.booking_document_delete),
    path("surgery-bookings/<int:pk>/documents/<int:did>/file", views.booking_document_file),
    path("surgery-bookings/<int:pk>/confirm", views.booking_confirm),
    path("surgery-bookings/<int:pk>/voucher", views.booking_voucher),
    path("surgery-recommendations", views.patient_surgery_recommendations),
    path("surgery-recommendations/<int:pk>/messages", views.patient_recommendation_messages),
]

doctor_patterns = [
    path("surgery-recommendations", views.doctor_surgery_recommendations),
    path("surgery-recommendations/<int:pk>/messages", views.doctor_recommendation_messages),
]

admin_patterns = [
    path("surgery-bookings", views.admin_surgery_booking_list),
    path("surgery-bookings/<int:pk>", views.admin_surgery_booking_detail),
    path("surgery-bookings/<int:pk>/documents/<int:did>/file", views.booking_document_file),
    path("surgery-recommendations", views.admin_surgery_recommendation_list),
    path("surgery-recommendations/<int:pk>", views.admin_surgery_recommendation_detail),
    path("surgery-recommendations/<int:pk>/messages", views.admin_recommendation_messages),
]
