from django.urls import path
from . import views

admin_patterns = [
    path("hospitals", views.admin_hospital_list),
    path("hospitals/<int:pk>", views.admin_hospital_detail),
    path("packages", views.admin_package_list),
    path("packages/<int:pk>", views.admin_package_detail),
]

public_patterns = [
    path("hospitals", views.public_hospital_list),
    path("packages", views.public_package_list),
    path("packages/<slug:slug>", views.public_package_detail),
]
