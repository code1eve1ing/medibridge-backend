from django.contrib import admin
from .models import SurgeryPackageBooking, PatientTravelInfo, TravelDocument, SurgeryCoupon


class TravelDocumentInline(admin.TabularInline):
    model = TravelDocument
    extra = 0
    readonly_fields = ["uploaded_at", "is_verified", "verified_by"]


@admin.register(SurgeryPackageBooking)
class SurgeryPackageBookingAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "package", "status", "tentative_date", "total_amount_usd"]
    list_filter = ["status"]
    inlines = [TravelDocumentInline]


@admin.register(PatientTravelInfo)
class PatientTravelInfoAdmin(admin.ModelAdmin):
    list_display = ["booking", "passport_country", "visa_required", "visa_status"]


@admin.register(SurgeryCoupon)
class SurgeryCouponAdmin(admin.ModelAdmin):
    list_display = ["booking", "code", "issued_at", "valid_from", "valid_until"]
    readonly_fields = ["code", "issued_at"]
