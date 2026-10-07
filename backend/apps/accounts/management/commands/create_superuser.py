"""Create a superuser without relying on interactive create_superuser quirks."""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a superuser identified by email (e.g. owner@pharmacy.local)."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Login email address")
        parser.add_argument(
            "--password",
            help="Password (omit to be prompted securely)",
        )
        parser.add_argument(
            "--username",
            help="Username (defaults to the email local part)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].strip().lower()

        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email '{email}' already exists.")

        username = (options.get("username") or email.split("@")[0]).strip()
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        password = options.get("password") or getpass("Password: ")
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters.")

        user = User.objects.create_superuser(
            username=username, email=email, password=password
        )
        self.stdout.write(
            self.style.SUCCESS(f"Superuser created: {user.email} (username: {user.username})")
        )
