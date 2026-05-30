from django.contrib import admin
from .models import Hospital, SurgeryPackage


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "state", "country", "is_partner"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SurgeryPackage)
class SurgeryPackageAdmin(admin.ModelAdmin):
    list_display = ["name", "hospital", "surgery_type", "price_usd", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ["surgery_type", "is_active", "hospital"]
