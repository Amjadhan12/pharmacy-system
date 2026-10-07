"""Authentication and profile endpoints."""
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    """JWT login. The username field is email (see accounts.User)."""


class MeView(APIView):
    """Return the profile of the currently authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
