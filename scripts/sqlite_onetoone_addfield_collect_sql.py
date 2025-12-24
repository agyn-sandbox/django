#!/usr/bin/env python3

"""Collect SQL emitted when adding a nullable OneToOneField on SQLite."""

from __future__ import annotations

import django
from django.conf import settings
from django.db import connection, models
from django.db.migrations.state import ModelState, ProjectState
from contextlib import contextmanager


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


def build_models() -> tuple[type[models.Model], type[models.Model], ProjectState]:
    state = ProjectState()
    refresh_state = ModelState(
        app_label="contenttypes",
        name="RefreshToken",
        fields=[("id", models.BigAutoField(primary_key=True))],
    )
    access_state = ModelState(
        app_label="contenttypes",
        name="AccessToken",
        fields=[("id", models.BigAutoField(primary_key=True))],
    )
    state.add_model(refresh_state)
    state.add_model(access_state)

    apps = state.apps
    refresh_model = apps.get_model("contenttypes", "RefreshToken")
    access_model = apps.get_model("contenttypes", "AccessToken")
    return refresh_model, access_model, state


@contextmanager
def patched_one_to_one_clone():
    original_clone = models.OneToOneField.clone

    def clone_with_resolved_remote(self):
        clone = original_clone(self)
        if isinstance(clone.remote_field.model, str) and not isinstance(self.remote_field.model, str):
            clone.remote_field.model = self.remote_field.model
        if getattr(clone.remote_field, "field_name", None) is None and getattr(self.remote_field, "field_name", None) is not None:
            clone.remote_field.field_name = self.remote_field.field_name
        clone.set_attributes_from_name(self.name)
        return clone

    models.OneToOneField.clone = clone_with_resolved_remote
    try:
        yield
    finally:
        models.OneToOneField.clone = original_clone


def collect_add_field_sql() -> list[str]:
    configure_settings()
    RefreshToken, AccessToken, state = build_models()

    with connection.schema_editor() as editor:
        editor.create_model(RefreshToken)
        editor.create_model(AccessToken)

    field = models.OneToOneField(
        RefreshToken,
        null=True,
        on_delete=models.CASCADE,
    )
    field.set_attributes_from_name("source_refresh_token")
    field.remote_field.model = RefreshToken
    AccessToken.add_to_class("source_refresh_token", field)

    with patched_one_to_one_clone():
        with connection.schema_editor(collect_sql=True) as editor:
            editor.add_field(AccessToken, field)
            return list(editor.collected_sql)


def main() -> None:
    statements = collect_add_field_sql()
    for statement in statements:
        print(statement)


if __name__ == "__main__":
    main()
