from django.contrib import admin

from .models import ConfigSnapshot


@admin.register(ConfigSnapshot)
class ConfigSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "config_type", "applied_successfully", "created_at")
    list_filter = ("config_type", "applied_successfully")
    search_fields = ("rendered_config",)
