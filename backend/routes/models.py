from django.db import models


class StaticRoute(models.Model):
    namespace = models.CharField(max_length=64)
    destination_cidr = models.CharField(max_length=64)
    next_hop = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.namespace}: {self.destination_cidr} via {self.next_hop}"
