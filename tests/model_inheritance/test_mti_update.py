import re

from django.db import connection, models
from django.db.models import OneToOneField, Q
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext, isolate_apps


@isolate_apps("model_inheritance")
class MultiParentUpdateTests(TransactionTestCase):
    reset_sequences = True
    available_apps = ["model_inheritance"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class PrimaryParent(models.Model):
            base_val = models.IntegerField(default=0)

            class Meta:
                app_label = "model_inheritance"

        class SecondaryParent(models.Model):
            otherbase_id = models.AutoField(primary_key=True)
            other_val = models.IntegerField(default=0)

            class Meta:
                app_label = "model_inheritance"

        class InheritedChild(PrimaryParent, SecondaryParent):
            child_val = models.IntegerField(default=0)

            class Meta:
                app_label = "model_inheritance"

        cls.PrimaryParent = PrimaryParent
        cls.SecondaryParent = SecondaryParent
        cls.Child = InheritedChild

        connection.disable_constraint_checking()
        try:
            with connection.schema_editor(atomic=False) as editor:
                editor.create_model(PrimaryParent)
                editor.create_model(SecondaryParent)
                editor.create_model(InheritedChild)
        finally:
            connection.enable_constraint_checking()

    @classmethod
    def tearDownClass(cls):
        try:
            connection.disable_constraint_checking()
            try:
                with connection.schema_editor(atomic=False) as editor:
                    editor.delete_model(cls.Child)
                    editor.delete_model(cls.SecondaryParent)
                    editor.delete_model(cls.PrimaryParent)
            finally:
                connection.enable_constraint_checking()
        finally:
            super().tearDownClass()

    def setUp(self):
        self.orphan_primary = self.PrimaryParent.objects.create(base_val=101)
        self.orphan_secondary = self.SecondaryParent.objects.create(other_val=202)
        self.detached_secondary = self.SecondaryParent.objects.create(other_val=303)
        self.child_one = self.Child.objects.create(
            base_val=1,
            other_val=10,
            child_val=100,
        )
        self.child_two = self.Child.objects.create(
            base_val=2,
            other_val=20,
            child_val=200,
        )
        link_field = self.Child._meta.get_ancestor_link(self.SecondaryParent)
        self.child_one_secondary_id = getattr(self.child_one, link_field.attname)
        self.child_two_secondary_id = getattr(self.child_two, link_field.attname)
        self.initial_secondary_pks = list(
            self.SecondaryParent.objects.order_by("pk").values_list("pk", flat=True)
        )

    def tearDown(self):
        self.Child.objects.all().delete()
        self.SecondaryParent.objects.all().delete()
        self.PrimaryParent.objects.all().delete()
        super().tearDown()

    def test_update_other_parent_targets_related_rows(self):
        self.assertCountEqual(
            self.initial_secondary_pks,
            [
                self.orphan_secondary.pk,
                self.detached_secondary.pk,
                self.child_one_secondary_id,
                self.child_two_secondary_id,
            ],
        )
        self.Child.objects.update(other_val=77)
        self.orphan_secondary.refresh_from_db()
        self.assertEqual(self.orphan_secondary.other_val, 202)
        self.detached_secondary.refresh_from_db()
        self.assertEqual(self.detached_secondary.other_val, 303)
        self.assertEqual(
            self.SecondaryParent.objects.get(pk=self.child_one_secondary_id).other_val,
            77,
        )
        self.assertEqual(
            self.SecondaryParent.objects.get(pk=self.child_two_secondary_id).other_val,
            77,
        )
        self.child_one.refresh_from_db()
        self.child_two.refresh_from_db()
        self.assertEqual(self.child_one.other_val, 77)
        self.assertEqual(self.child_two.other_val, 77)

    def test_update_base_parent_targets_related_rows(self):
        self.Child.objects.update(base_val=88)
        self.orphan_primary.refresh_from_db()
        self.assertEqual(self.orphan_primary.base_val, 101)
        self.assertEqual(
            self.PrimaryParent.objects.get(pk=self.child_one.pk).base_val,
            88,
        )
        self.assertEqual(
            self.PrimaryParent.objects.get(pk=self.child_two.pk).base_val,
            88,
        )

    def test_filtered_updates_respect_query(self):
        self.Child.objects.filter(child_val=100).update(other_val=55)
        self.Child.objects.filter(Q(child_val=200) | Q(other_val=55)).update(
            base_val=66
        )

        self.orphan_secondary.refresh_from_db()
        self.assertEqual(self.orphan_secondary.other_val, 202)
        self.detached_secondary.refresh_from_db()
        self.assertEqual(self.detached_secondary.other_val, 303)
        self.assertEqual(
            self.SecondaryParent.objects.get(pk=self.child_one_secondary_id).other_val,
            55,
        )
        self.assertEqual(
            self.SecondaryParent.objects.get(pk=self.child_two_secondary_id).other_val,
            20,
        )
        self.orphan_primary.refresh_from_db()
        self.assertEqual(self.orphan_primary.base_val, 101)
        self.assertEqual(
            self.PrimaryParent.objects.get(pk=self.child_one.pk).base_val,
            66,
        )
        self.assertEqual(
            self.PrimaryParent.objects.get(pk=self.child_two.pk).base_val,
            66,
        )

    def test_parent_updates_constrain_to_child_ids_in_sql(self):
        parent_links = {}
        for model in (self.PrimaryParent, self.SecondaryParent):
            link = self.Child._meta.get_ancestor_link(model)
            self.assertIsInstance(link, OneToOneField)
            parent_links[model] = link

        expected_ids_by_table = {
            model._meta.db_table: {
                getattr(self.child_one, link.attname),
                getattr(self.child_two, link.attname),
            }
            for model, link in parent_links.items()
        }

        with CaptureQueriesContext(connection) as ctx:
            self.Child.objects.filter(
                pk__in=[self.child_one.pk, self.child_two.pk]
            ).update(
                base_val=33,
                other_val=44,
            )

        queries = list(ctx.captured_queries)

        placeholder_pattern = re.compile(r"(%\([^)]+\)s|%s|\?|:\d+)")

        def normalized_table_from_sql(sql):
            match = re.match(
                r"^\s*UPDATE\s+(?P<table>(?:\"[^\"]+\"|`[^`]+`|\[[^\]]+\]|[\w]+)"
                r"(?:\.(?:\"[^\"]+\"|`[^`]+`|\[[^\]]+\]|[\w]+))?)\s+SET",
                sql,
                flags=re.IGNORECASE,
            )
            if not match:
                return None
            identifier = match.group("table")
            parts = [part.strip('"`[]') for part in identifier.split('.')]
            return parts[-1]

        def extract_in_values(sql, params, expected_count):
            where_match = re.search(r"\bWHERE\b", sql, flags=re.IGNORECASE)
            placeholder_count = 0
            if where_match:
                set_clause = sql[: where_match.start()]
                placeholder_count = len(placeholder_pattern.findall(set_clause))
            extracted = []
            if params:
                param_list = list(params)
                where_params = param_list[placeholder_count:]
                if where_params:
                    relevant = where_params[-expected_count:]
                    for value in relevant:
                        try:
                            extracted.append(int(value))
                        except (TypeError, ValueError):
                            extracted.append(value)
            if extracted:
                return set(extracted)
            in_match = re.search(
                r"\bIN\s*\((?P<values>[^)]+)\)",
                sql,
                flags=re.IGNORECASE,
            )
            if not in_match:
                return set()
            tokens = [
                token.strip()
                for token in in_match.group("values").split(',')
                if token.strip()
            ]
            parsed = set()
            for token in tokens:
                normalized = token.strip('"\'')
                try:
                    parsed.add(int(normalized))
                except ValueError:
                    if normalized:
                        parsed.add(normalized)
            return parsed

        inspected_tables = set()
        for query in queries:
            sql = query["sql"]
            if "UPDATE" not in sql.upper():
                continue
            table = normalized_table_from_sql(sql)
            if table not in expected_ids_by_table:
                continue
            expected_ids = expected_ids_by_table[table]
            actual_ids = extract_in_values(sql, query.get("params"), len(expected_ids))
            self.assertEqual(
                actual_ids,
                expected_ids,
                f"{table} UPDATE should target {expected_ids}",
            )
            inspected_tables.add(table)

        self.assertEqual(inspected_tables, set(expected_ids_by_table))
