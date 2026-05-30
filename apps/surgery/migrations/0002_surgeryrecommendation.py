import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0005_appointment_fee_waived_and_more"),
        ("doctors", "0002_doctoravailabilityslot"),
        ("hospitals", "0001_initial"),
        ("patients", "0001_initial"),
        ("surgery", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SurgeryRecommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="surgery_recommendations", to="doctors.doctorprofile")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="surgery_recommendations", to="patients.patientprofile")),
                ("package", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="hospitals.surgerypackage")),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="surgery_recommendations", to="consultations.appointment")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
