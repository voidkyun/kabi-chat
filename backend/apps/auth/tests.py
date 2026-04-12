from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .services import AuthError, JWTService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def configured_discord_env(monkeypatch):
    monkeypatch.setenv("DISCORD_CLIENT_ID", "discord-client-id")
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", "discord-client-secret")
    monkeypatch.setenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/discord/callback")


@pytest.fixture
def authenticated_client(api_client):
    user_model = get_user_model()
    user = user_model.objects.create_user(username="alice", password="password123")
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "method", "expected_status"),
    [
        ("healthz", "get", status.HTTP_200_OK),
        ("discord-login", "get", status.HTTP_200_OK),
        ("discord-callback", "get", status.HTTP_400_BAD_REQUEST),
        ("token-refresh", "post", status.HTTP_401_UNAUTHORIZED),
        ("auth-logout", "post", status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_public_endpoints_remain_accessible_without_authentication(
    api_client, configured_discord_env, url_name, method, expected_status
):
    response = getattr(api_client, method)(reverse(url_name))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "method"),
    [
        ("auth-me", "get"),
        ("workspace-list", "get"),
        ("channel-list", "get"),
        ("message-list", "get"),
        ("macro-list", "get"),
    ],
)
def test_domain_endpoints_require_authentication(api_client, url_name, method):
    response = getattr(api_client, method)(reverse(url_name))

    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }


@pytest.mark.django_db
def test_auth_me_returns_authenticated_user(authenticated_client):
    api_client, user = authenticated_client

    response = api_client.get(reverse("auth-me"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "authenticated": True,
        "id": user.id,
        "username": user.get_username(),
        "display_name": user.get_username(),
        "avatar_url": "",
        "discord_user_id": None,
    }


@pytest.mark.django_db
def test_discord_login_returns_authorization_url_and_state_cookie(api_client, configured_discord_env):
    response = api_client.get(reverse("discord-login"))

    payload = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert payload["provider"] == "discord"
    assert payload["authorization_url"].startswith("https://discord.com/oauth2/authorize?")
    assert payload["state"]
    assert "client_id=discord-client-id" in payload["authorization_url"]
    assert "state=" in payload["authorization_url"]
    assert response.cookies["kabi_chat_oauth_state"].value
    assert response.cookies["kabi_chat_oauth_state"]["httponly"]
    assert response.cookies["kabi_chat_oauth_state"]["samesite"] == "Lax"


@pytest.mark.django_db
def test_discord_callback_issues_tokens_and_sets_refresh_cookie(
    api_client,
    configured_discord_env,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.exchange_code",
        lambda self, code: {"access_token": "discord-access-token"},
    )
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.fetch_user",
        lambda self, access_token: {
            "discord_user_id": "12345",
            "discord_username": "kabi",
            "display_name": "Kabi",
            "avatar_url": "https://cdn.discordapp.com/avatars/12345/avatar.png",
        },
    )

    login_response = api_client.get(reverse("discord-login"))
    state = login_response.json()["state"]

    callback_response = api_client.get(
        reverse("discord-callback"),
        {"code": "valid-code", "state": state},
    )

    payload = callback_response.json()
    assert callback_response.status_code == status.HTTP_200_OK
    assert payload["token_type"] == "Bearer"
    assert payload["expires_in"] > 0
    assert payload["access_token"]
    assert payload["user"]["username"] == "discord_12345"
    assert payload["user"]["display_name"] == "Kabi"
    assert payload["user"]["avatar_url"] == "https://cdn.discordapp.com/avatars/12345/avatar.png"
    assert payload["user"]["discord_user_id"] == "12345"
    assert payload["user"]["id"] > 0
    assert callback_response.cookies["kabi_chat_refresh_token"].value
    assert callback_response.cookies["kabi_chat_refresh_token"]["httponly"]

    me_response = api_client.get(
        reverse("auth-me"),
        HTTP_AUTHORIZATION=f"Bearer {payload['access_token']}",
    )
    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["discord_user_id"] == "12345"


@pytest.mark.django_db
def test_discord_callback_rejects_access_denied(api_client, configured_discord_env):
    response = api_client.get(reverse("discord-callback"), {"error": "access_denied"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error": "discord_access_denied",
        "detail": "Discord authorization was denied.",
    }


@pytest.mark.django_db
def test_discord_callback_rejects_invalid_state(
    api_client,
    configured_discord_env,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.exchange_code",
        lambda self, code: {"access_token": "discord-access-token"},
    )
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.fetch_user",
        lambda self, access_token: {
            "discord_user_id": "12345",
            "discord_username": "kabi",
            "display_name": "Kabi",
            "avatar_url": "",
        },
    )

    login_response = api_client.get(reverse("discord-login"))
    assert login_response.status_code == status.HTTP_200_OK

    callback_response = api_client.get(
        reverse("discord-callback"),
        {"code": "valid-code", "state": "wrong-state"},
    )

    assert callback_response.status_code == status.HTTP_400_BAD_REQUEST
    assert callback_response.json() == {
        "error": "invalid_state",
        "detail": "OAuth state did not match.",
    }


@pytest.mark.django_db
def test_discord_callback_rejects_invalid_authorization_code(
    api_client,
    configured_discord_env,
    monkeypatch,
):
    def raise_invalid_code(self, code):
        raise AuthError("invalid_authorization_code", "Invalid authorization code.", 400)

    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.exchange_code",
        raise_invalid_code,
    )

    login_response = api_client.get(reverse("discord-login"))
    state = login_response.json()["state"]

    callback_response = api_client.get(
        reverse("discord-callback"),
        {"code": "expired-code", "state": state},
    )

    assert callback_response.status_code == status.HTTP_400_BAD_REQUEST
    assert callback_response.json() == {
        "error": "invalid_authorization_code",
        "detail": "Invalid authorization code.",
    }


@pytest.mark.django_db
def test_refresh_rotates_refresh_token(api_client, configured_discord_env, monkeypatch):
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.exchange_code",
        lambda self, code: {"access_token": "discord-access-token"},
    )
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.fetch_user",
        lambda self, access_token: {
            "discord_user_id": "12345",
            "discord_username": "kabi",
            "display_name": "Kabi",
            "avatar_url": "",
        },
    )

    state = api_client.get(reverse("discord-login")).json()["state"]
    callback_response = api_client.get(reverse("discord-callback"), {"code": "valid-code", "state": state})
    old_refresh_token = callback_response.cookies["kabi_chat_refresh_token"].value

    refresh_response = api_client.post(reverse("token-refresh"))

    assert refresh_response.status_code == status.HTTP_200_OK
    new_refresh_token = refresh_response.cookies["kabi_chat_refresh_token"].value
    assert new_refresh_token
    assert new_refresh_token != old_refresh_token

    stale_client = APIClient()
    stale_client.cookies["kabi_chat_refresh_token"] = old_refresh_token
    stale_response = stale_client.post(reverse("token-refresh"))

    assert stale_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert stale_response.json() == {
        "error": "invalid_refresh_token",
        "detail": "Refresh token is invalid.",
    }


@pytest.mark.django_db
def test_logout_revokes_refresh_token(api_client, configured_discord_env, monkeypatch):
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.exchange_code",
        lambda self, code: {"access_token": "discord-access-token"},
    )
    monkeypatch.setattr(
        "apps.auth.services.DiscordOAuthService.fetch_user",
        lambda self, access_token: {
            "discord_user_id": "12345",
            "discord_username": "kabi",
            "display_name": "Kabi",
            "avatar_url": "",
        },
    )

    state = api_client.get(reverse("discord-login")).json()["state"]
    callback_response = api_client.get(reverse("discord-callback"), {"code": "valid-code", "state": state})
    refresh_token = callback_response.cookies["kabi_chat_refresh_token"].value

    logout_response = api_client.post(reverse("auth-logout"))

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {"detail": "Logged out."}

    stale_client = APIClient()
    stale_client.cookies["kabi_chat_refresh_token"] = refresh_token
    refresh_response = stale_client.post(reverse("token-refresh"))

    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert refresh_response.json() == {
        "error": "invalid_refresh_token",
        "detail": "Refresh token is invalid.",
    }


@pytest.mark.django_db
def test_auth_me_rejects_expired_access_token(api_client):
    user_model = get_user_model()
    user = user_model.objects.create_user(username="bob", password="password123")
    expired_token = JWTService().issue_access_token(
        user,
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    response = api_client.get(
        reverse("auth-me"),
        HTTP_AUTHORIZATION=f"Bearer {expired_token}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error": "access_token_expired",
        "detail": "Access token has expired.",
    }
