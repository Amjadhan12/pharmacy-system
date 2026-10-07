from django.test import TestCase
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """The health endpoint must prove API + database connectivity."""

    def setUp(self):
        self.client = APIClient()

    def test_health_returns_ok_when_database_available(self):
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["service"], "pharmafin-api")
        self.assertEqual(payload["data"]["status"], "ok")
        self.assertEqual(payload["data"]["database"], "ok")

    def test_health_is_public(self):
        """Health endpoint must not require authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
