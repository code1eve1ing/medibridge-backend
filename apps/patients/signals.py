from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from .models import PatientProfile


@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    if created and instance.role == "patient":
        PatientProfile.objects.create(user=instance)
