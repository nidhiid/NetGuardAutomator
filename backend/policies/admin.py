from django.contrib import admin

from .models import FirewallRule


@admin.register(FirewallRule)
class FirewallRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "source_ip", "destination_ip", "protocol", "port", "action", "enabled", "created_at")
    list_filter = ("action", "enabled", "protocol")
    search_fields = ("source_ip", "destination_ip")
