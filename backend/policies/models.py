from django.db import models


class FirewallRule(models.Model):
    ACTION_ALLOW = "ALLOW"
    ACTION_DENY = "DENY"
    ACTION_CHOICES = [
        (ACTION_ALLOW, "Allow"),
        (ACTION_DENY, "Deny"),
    ]

    source_ip = models.CharField(max_length=64)
    destination_ip = models.CharField(max_length=64)
    protocol = models.CharField(max_length=16)
    port = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        port = f":{self.port}" if self.port else ""
        return f"{self.action} {self.protocol} {self.source_ip} -> {self.destination_ip}{port}"
