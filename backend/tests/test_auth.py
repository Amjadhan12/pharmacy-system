from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role

User = get_user_model()


class AuthenticationTests(TestCase):
    """JWT authentication via email (accounts.User.USERNAME_FIELD = email)."""

    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name="Pharmacist", code="pharmacist")
        self.password = "S3cure-Pass!"
        self.user = User.objects.create_user(
            username="jane",
            email="jane@pharmafin.test",
            password=self.password,
            first_name="Jane",
            last_name="Doe",
            role=self.role,
        )

    def test_login_with_email_returns_jwt_tokens(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("access", payload["data"])
        self.assertIn("refresh", payload["data"])

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("message", payload)
        # Error envelope must not leak internals.
        self.assertNotIn("traceback", str(payload).lower())

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_me_returns_profile_with_role(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["email"], self.user.email)
        self.assertEqual(payload["data"]["full_name"], "Jane Doe")
        self.assertEqual(payload["data"]["role"]["code"], "pharmacist")
