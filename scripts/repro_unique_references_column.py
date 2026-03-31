"""Reproduce Statement.references_column() failure for unique constraints."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.db import connection, models  # noqa: E402


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
        INSTALLED_APPS=["django.contrib.contenttypes", "tests"],
        SECRET_KEY="not-secret",
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    django.setup()


def get_author_model() -> type[models.Model]:
    class Author(models.Model):
        email = models.CharField(max_length=255)

        class Meta:
            app_label = "tests"
            db_table = "repro_author"

    return Author


def main() -> None:
    configure_settings()
    Author = get_author_model()
    field = Author._meta.get_field("email")

    with connection.schema_editor() as editor:
        statement = editor._create_unique_sql(
            Author,
            [field.column],
            name="author_email_unique",
        )

    table = Author._meta.db_table
    column = field.column

    assert statement.references_column(
        table, column
    ), f"Expected references_column({table!r}, {column!r}) to be True"

    print(
        "references_column() returned True for unique constraint on %s.%s"
        % (table, column)
    )


if __name__ == "__main__":
    main()
