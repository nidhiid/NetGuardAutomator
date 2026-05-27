from django.contrib import admin

from .models import StaticRoute


@admin.register(StaticRoute)
class StaticRouteAdmin(admin.ModelAdmin):
    list_display = ("id", "namespace", "destination_cidr", "next_hop", "created_at")
    search_fields = ("namespace", "destination_cidr", "next_hop")
