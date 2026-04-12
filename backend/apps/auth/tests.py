from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class AnonymousAccessPolicyTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_public_endpoints_remain_accessible_without_authentication(self):
        public_cases = [
            (reverse("healthz"), "get", status.HTTP_200_OK),
            (reverse("discord-login"), "get", status.HTTP_501_NOT_IMPLEMENTED),
            (reverse("discord-callback"), "get", status.HTTP_501_NOT_IMPLEMENTED),
        ]

        for url, method, expected_status in public_cases:
            with self.subTest(url=url, method=method):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, expected_status)

    def test_domain_and_auth_management_endpoints_require_authentication(self):
        protected_cases = [
            (reverse("auth-me"), "get"),
            (reverse("token-refresh"), "post"),
            (reverse("auth-logout"), "post"),
            (reverse("workspace-list"), "get"),
            (reverse("channel-list"), "get"),
            (reverse("message-list"), "get"),
            (reverse("macro-list"), "get"),
        ]

        for url, method in protected_cases:
            with self.subTest(url=url, method=method):
                response = getattr(self.client, method)(url)
                self.assertIn(
                    response.status_code,
                    {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
                )
