from . import PostgreSQLTestCase
from .models import MixedCaseColumns


class BulkCreateConflictDbColumnTests(PostgreSQLTestCase):
    def test_bulk_create_updates_with_db_column_names(self):
        MixedCaseColumns.objects.create(blacklistid=1, sectorid=1)

        MixedCaseColumns.objects.bulk_create(
            [
                MixedCaseColumns(blacklistid=1, sectorid=2),
                MixedCaseColumns(blacklistid=2, sectorid=3),
            ],
            update_conflicts=True,
            update_fields=["sectorid"],
            unique_fields=["blacklistid"],
        )

        self.assertSequenceEqual(
            MixedCaseColumns.objects.order_by("blacklistid").values_list(
                "blacklistid", "sectorid"
            ),
            [(1, 2), (2, 3)],
        )
