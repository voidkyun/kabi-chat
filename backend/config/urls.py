from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "apps": ["auth", "workspaces", "channels", "messages", "macros"],
            }
        )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", HealthCheckView.as_view(), name="healthz"),
    path("auth/", include("apps.auth.urls")),
    path("workspaces/", include("apps.workspaces.urls")),
    path("channels/", include("apps.channels.urls")),
    path("messages/", include("apps.messages.urls")),
    path("macros/", include("apps.macros.urls")),
]
