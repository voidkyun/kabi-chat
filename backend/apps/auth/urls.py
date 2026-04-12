from django.urls import path

from .views import CurrentUserView, DiscordCallbackView, DiscordLoginView, LogoutView, TokenRefreshView


urlpatterns = [
    path("discord/login", DiscordLoginView.as_view(), name="discord-login"),
    path("discord/callback", DiscordCallbackView.as_view(), name="discord-callback"),
    path("me", CurrentUserView.as_view(), name="auth-me"),
    path("token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
]
