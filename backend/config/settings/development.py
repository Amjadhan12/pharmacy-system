"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Development fallback key - production settings refuse to start without one.
if not SECRET_KEY:  # noqa: F405
    SECRET_KEY = "dev-only-insecure-key-change-before-production"

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
