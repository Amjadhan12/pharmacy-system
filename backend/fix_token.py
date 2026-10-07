import json
import os
import sys

sys.path.insert(0, r"E:\my projects\pharmacy-system\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django  # noqa: E402

django.setup()
from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

u = get_user_model().objects.get(id=1)
r = RefreshToken.for_user(u)
print("NEW_ACCESS=" + str(r.access_token))
print("NEW_REFRESH=" + str(r))
