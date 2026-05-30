from django.db import models


class EmailNotification(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    body_text = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    error = models.TextField(blank=True)
    context_type = models.CharField(max_length=50, blank=True)
    context_id = models.PositiveIntegerField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.to_email} — {self.subject} [{self.status}]"
