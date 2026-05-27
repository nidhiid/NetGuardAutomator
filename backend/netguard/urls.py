from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from configs.views import ApplyConfigView, ConfigSnapshotViewSet, RollbackConfigView
from monitoring.views import SecurityAlertViewSet
from policies.views import FirewallRuleViewSet
from routes.views import StaticRouteViewSet


router = DefaultRouter()
router.register("firewall-rules", FirewallRuleViewSet, basename="firewall-rule")
router.register("routes", StaticRouteViewSet, basename="route")
router.register("config-history", ConfigSnapshotViewSet, basename="config-snapshot")
router.register("alerts", SecurityAlertViewSet, basename="alert")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/apply-config/", ApplyConfigView.as_view(), name="apply-config"),
    path("api/rollback/<int:snapshot_id>/", RollbackConfigView.as_view(), name="rollback-config"),
]
