#!/usr/bin/env python3

"""Collect SQL emitted when adding a nullable OneToOneField on SQLite."""

from __future__ import annotations

import django
from django.apps.registry import Apps
from django.conf import settings
from django.db import connection, models


def configure_settings() -> None:
    if settings.configured:
        return
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=["django.contrib.contenttypes"],
        SECRET_KEY="sqlite-add-field-repro",
    )
    django.setup()


def build_models(apps: Apps) -> tuple[type[models.Model], type[models.Model]]:
    refresh_meta = type("Meta", (), {"app_label": "repro_app", "apps": apps})
    access_meta = type("Meta", (), {"app_label": "repro_app", "apps": apps})

    RefreshToken = type(
        "RefreshToken",
        (models.Model,),
        {
            "__module__": __name__,
            "id": models.BigAutoField(primary_key=True),
            "Meta": refresh_meta,
        },
    )

    AccessToken = type(
        "AccessToken",
        (models.Model,),
        {
            "__module__": __name__,
            "id": models.BigAutoField(primary_key=True),
            "Meta": access_meta,
        },
    )

    return RefreshToken, AccessToken


def collect_add_field_sql() -> list[str]:
    configure_settings()
    apps = Apps()
    RefreshToken, AccessToken = build_models(apps)

    with connection.schema_editor() as editor:
        editor.create_model(RefreshToken)
        editor.create_model(AccessToken)

    field = models.OneToOneField(
        RefreshToken,
        null=True,
        on_delete=models.CASCADE,
    )
    field.set_attributes_from_name("source_refresh_token")
    AccessToken.add_to_class("source_refresh_token", field)

    with connection.schema_editor(collect_sql=True) as editor:
        editor.add_field(AccessToken, field)
        return list(editor.collected_sql)


def main() -> None:
    statements = collect_add_field_sql()
    for statement in statements:
        print(statement)


if __name__ == "__main__":
    main()
