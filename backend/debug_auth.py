import os
import sys
import json

print("ENV_DJANGO_SETTINGS_MODULE =", os.environ.get("DJANGO_SETTINGS_MODULE"))
sys.path.insert(0, r"E:\my projects\pharmacy-system\backend")
import django

django.setup()
from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

u = get_user_model().objects.get(id=1)
r = RefreshToken.for_user(u)
TOKEN = str(r.access_token)
print("TOKEN=" + TOKEN)

import urllib.request
import urllib.error

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/me/",
    headers={"Authorization": "Bearer " + TOKEN},
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("AUTH_OK", resp.status, resp.read()[:200])
except urllib.error.HTTPError as e:
    print("AUTH_HTTP", e.code)
    print(e.read().decode())
