from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Shared application configuration for the ``common`` package."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self) -> None:  # pragma: no cover - environment compatibility shim
        # ------------------------------------------------------------------
        # MariaDB 10.4 compatibility shim for LOCAL DEVELOPMENT ONLY.
        #
        # The local XAMPP server ships MariaDB 10.4.32 while Django >= 5.1
        # only supports MariaDB >= 10.5. Two things must be adjusted:
        #
        # 1. check_database_version_supported: the version gate exists only
        #    because MariaDB 10.4 reached upstream EOL (Django ticket #34850,
        #    "Cleanup/optimization" - not a technical requirement).
        # 2. can_return_columns_from_insert: Django enables INSERT ... RETURNING
        #    for every MariaDB it supports, but RETURNING was added in
        #    MariaDB 10.5. Disabling it makes Django use the classic
        #    INSERT + LAST_INSERT_ID() path, which works on 10.4.
        #
        # REMOVE this shim once the database server is upgraded to
        # MariaDB >= 10.11 / MySQL >= 8.0 (also required for Django 6.x).
        # See docs/development.md.
        # ------------------------------------------------------------------
        from django.db.backends.mysql.base import DatabaseWrapper
        from django.db.backends.mysql.features import DatabaseFeatures

        DatabaseWrapper.check_database_version_supported = lambda self: None
        DatabaseFeatures.can_return_columns_from_insert = False

