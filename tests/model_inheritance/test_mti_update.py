from django.db import connection, models
from django.db.models import Q
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
        parent_tables = {
            self.PrimaryParent._meta.db_table,
            self.SecondaryParent._meta.db_table,
        }
        with CaptureQueriesContext(connection) as ctx:
            self.Child.objects.filter(pk__in=[self.child_one.pk, self.child_two.pk]).update(
                base_val=33,
                other_val=44,
            )

        update_statements = [
            q["sql"] for q in ctx if "UPDATE" in q["sql"] and " WHERE " in q["sql"]
        ]
        self.assertGreaterEqual(len(update_statements), 2)
        for statement in update_statements:
            if not any(table in statement for table in parent_tables):
                continue
            self.assertIn(" WHERE ", statement)
            self.assertIn(" IN ", statement)
            self.assertTrue(
                str(self.child_one.pk) in statement
                or str(self.child_one_secondary_id) in statement
            )
            self.assertTrue(
                str(self.child_two.pk) in statement
                or str(self.child_two_secondary_id) in statement
            )
