from django.db import models
from django.utils.text import slugify


class Hospital(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    description = models.TextField()
    image = models.ImageField(upload_to="hospitals/", null=True, blank=True)
    accreditations = models.CharField(max_length=255, blank=True, help_text="Comma-separated")
    website = models.URLField(blank=True)
    is_partner = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Hospital.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class SurgeryPackage(models.Model):
    FLIGHT_CLASS_CHOICES = [("economy", "Economy"), ("business", "Business")]
    ACCOMMODATION_CHOICES = [
        ("hotel_3star", "3-Star Hotel"),
        ("hotel_4star", "4-Star Hotel"),
        ("serviced_apt", "Serviced Apartment"),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    surgery_type = models.CharField(max_length=100)
    description = models.TextField()
    total_duration_days = models.PositiveSmallIntegerField()
    hospital_stay_days = models.PositiveSmallIntegerField()
    recovery_stay_days = models.PositiveSmallIntegerField()
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    includes_flight = models.BooleanField(default=False)
    flight_class = models.CharField(max_length=10, choices=FLIGHT_CLASS_CHOICES, default="economy")
    includes_visa_assistance = models.BooleanField(default=False)
    includes_accommodation = models.BooleanField(default=False)
    accommodation_type = models.CharField(max_length=15, choices=ACCOMMODATION_CHOICES, default="hotel_3star")
    includes_transport = models.BooleanField(default=False)
    includes_meals = models.BooleanField(default=False)
    inclusions_text = models.TextField(blank=True, help_text="One item per line")
    exclusions_text = models.TextField(blank=True, help_text="One item per line")
    image = models.ImageField(upload_to="packages/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_usd"]

    def __str__(self):
        return f"{self.name} ({self.hospital.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while SurgeryPackage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
