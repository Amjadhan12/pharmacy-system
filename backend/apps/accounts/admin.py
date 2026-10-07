from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AuditLog,
    LoginActivity,
    Permission,
    Role,
    RolePermission,
    User,
    UserBranch,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_system", "created_at")
    search_fields = ("name", "code")
    list_filter = ("is_system",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "module")
    search_fields = ("code", "name", "module")
    list_filter = ("module",)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")
    list_filter = ("role",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
    )
    search_fields = ("email", "username", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "role")
    ordering = ("email",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "PharmaFin",
            {"fields": ("role", "phone", "avatar")},
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "PharmaFin",
            {"fields": ("email", "first_name", "last_name", "role", "phone")},
        ),
    )


@admin.register(UserBranch)
class UserBranchAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "is_default")
    list_filter = ("is_default",)


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("email", "success", "ip_address", "created_at")
    list_filter = ("success",)
    search_fields = ("email", "ip_address")
    readonly_fields = ("email", "ip_address", "user_agent", "success", "message", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "object_type", "object_repr", "actor_repr")
    list_filter = ("action", "object_type")
    search_fields = ("object_repr", "actor_repr", "object_id")
    readonly_fields = (
        "actor",
        "actor_repr",
        "action",
        "object_type",
        "object_id",
        "object_repr",
        "changes",
        "ip_address",
        "created_at",
    )
