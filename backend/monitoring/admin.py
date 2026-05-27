from django.contrib import admin

from .models import SecurityAlert


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ("id", "alert_type", "severity", "created_at")
    list_filter = ("severity", "alert_type")
    search_fields = ("alert_type", "description")
