from django.contrib import admin
from .models import DoctorProfile, DoctorEducation, Specialization, DoctorInvite

admin.site.register(Specialization)
admin.site.register(DoctorProfile)
admin.site.register(DoctorEducation)
admin.site.register(DoctorInvite)
