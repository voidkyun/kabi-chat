from os import getenv

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class DiscordLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "provider": "discord",
                "redirect_uri": getenv("DISCORD_REDIRECT_URI", ""),
                "detail": "Discord OAuth2 integration is not implemented yet.",
            },
            status=501,
        )


class DiscordCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"detail": "Discord OAuth2 callback is not implemented yet."},
            status=501,
        )


class CurrentUserView(APIView):
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({"authenticated": False}, status=401)

        return Response(
            {
                "authenticated": True,
                "id": request.user.id,
                "username": request.user.get_username(),
            }
        )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"detail": "JWT refresh is not implemented yet."}, status=501)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"detail": "Logout is not implemented yet."}, status=501)
