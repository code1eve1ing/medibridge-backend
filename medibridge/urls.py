from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core import urls as core_urls
from apps.doctors import urls as doctor_urls
from apps.consultations import urls as consultation_urls
from apps.hospitals import urls as hospital_urls
from apps.surgery import urls as surgery_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/patient/", include("apps.patients.urls")),
    path("api/v1/patient/", include((doctor_urls.patient_patterns, "patient-doctor"))),
    path("api/v1/patient/", include((consultation_urls.patient_patterns, "consultation-patient"))),
    path("api/v1/doctor/", include((doctor_urls.doctor_patterns, "doctor"))),
    path("api/v1/doctor/", include((consultation_urls.doctor_patterns, "consultation-doctor"))),
    path("api/v1/admin/", include((doctor_urls.admin_patterns, "api-admin"))),
    path("api/v1/admin/", include((consultation_urls.admin_patterns, "consultation-admin"))),
    path("api/v1/admin/", include((hospital_urls.admin_patterns, "hospital-admin"))),
    path("api/v1/admin/", include((core_urls.admin_patterns, "core-admin"))),
    path("api/v1/public/", include((hospital_urls.public_patterns, "hospital-public"))),
    path("api/v1/patient/", include((surgery_urls.patient_patterns, "surgery-patient"))),
    path("api/v1/doctor/", include((surgery_urls.doctor_patterns, "surgery-doctor"))),
    path("api/v1/admin/", include((surgery_urls.admin_patterns, "surgery-admin"))),
    path("api/v1/dev/", include((consultation_urls.dev_patterns, "dev"))),
    path("api/v1/public/", include((doctor_urls.public_patterns, "public"))),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
