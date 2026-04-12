import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


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
        ("discord-login", "get", status.HTTP_501_NOT_IMPLEMENTED),
        ("discord-callback", "get", status.HTTP_501_NOT_IMPLEMENTED),
        ("token-refresh", "post", status.HTTP_501_NOT_IMPLEMENTED),
        ("auth-logout", "post", status.HTTP_501_NOT_IMPLEMENTED),
    ],
)
def test_public_endpoints_remain_accessible_without_authentication(
    api_client, url_name, method, expected_status
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
    }
