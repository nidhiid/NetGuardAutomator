from django.db import models


class ConfigSnapshot(models.Model):
    config_type = models.CharField(max_length=64)
    rendered_config = models.TextField()
    applied_successfully = models.BooleanField(default=False)
    ansible_stdout = models.TextField(blank=True)
    ansible_stderr = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        status = "applied" if self.applied_successfully else "pending"
        return f"{self.config_type} snapshot {self.id} ({status})"
