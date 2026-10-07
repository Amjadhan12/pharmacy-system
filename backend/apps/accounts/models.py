"""Accounts, RBAC and audit models."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from common.utils import TimeStampedModel


class Role(TimeStampedModel):
    """A named role used for role-based access control."""

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="Seeded system role (e.g. Super Admin, Pharmacy Owner).",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Permission(TimeStampedModel):
    """Granular permission granted to roles via RolePermission."""

    code = models.CharField(max_length=100, unique=True)  # e.g. "sales.create"
    name = models.CharField(max_length=150)
    module = models.CharField(max_length=50, db_index=True)  # e.g. "sales"
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["module", "code"]
        verbose_name_plural = "permissions"

    def __str__(self) -> str:
        return self.code


class RolePermission(TimeStampedModel):
    """M2M join between Role and Permission."""

    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="role_permissions"
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        ordering = ["role__code", "permission__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="uniq_role_permission"
            )
        ]

    def __str__(self) -> str:
        return f"{self.role.code}: {self.permission.code}"


class User(AbstractUser):
    """System user. Email is the login identifier (USERNAME_FIELD)."""

    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.username

    @property
    def role_code(self) -> str | None:
        return self.role.code if self.role else None

    def has_role(self, *codes: str) -> bool:
        """Return True if the user's role code is one of ``codes``."""
        if self.is_superuser:
            return True
        return bool(self.role and self.role.code in codes)


class UserBranch(TimeStampedModel):
    """Assigns a user to one or more branches of a pharmacy."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_branches",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="user_branches",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "branch"], name="uniq_user_branch"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.branch}"


class LoginActivity(models.Model):
    """Record of every login attempt (successful or not)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_activities",
    )
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False, db_index=True)
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} - {'ok' if self.success else 'failed'}"


class AuditLog(models.Model):
    """Append-only audit trail of important actions."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_repr = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=100, db_index=True)  # create/update/delete/...
    object_type = models.CharField(max_length=100, db_index=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True, db_index=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(null=True, blank=True)  # {"before": {...}, "after": {...}}
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} {self.object_type} by {self.actor_repr or 'system'}"

