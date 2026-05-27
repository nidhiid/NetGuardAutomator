from django.db import models


class SecurityAlert(models.Model):
    alert_type = models.CharField(max_length=64)
    severity = models.CharField(max_length=32)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.severity}: {self.alert_type}"
