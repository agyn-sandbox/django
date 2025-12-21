from sqlite3 import dbapi2 as Database

from django.core import checks
from django.db.backends.base.validation import BaseDatabaseValidation


class DatabaseValidation(BaseDatabaseValidation):
    def check(self, **kwargs):
        issues = super().check(**kwargs)
        issues.extend(self._check_sqlite_version())
        return issues

    def _check_sqlite_version(self):
        if Database.sqlite_version_info < (3, 9, 0):
            return [checks.Error(
                "SQLite 3.9.0 or later is required (found %s)." % Database.sqlite_version,
                hint=(
                    "Upgrade SQLite to ≥ 3.9.0 or switch to a supported database backend."
                ),
                id='sqlite.E001',
            )]
        return []
