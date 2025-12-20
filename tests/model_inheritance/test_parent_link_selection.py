from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps


class ParentLinkSelectionTests(SimpleTestCase):
    @isolate_apps('model_inheritance')
    def test_parent_link_selected_regardless_of_field_order(self):
        class Parent(models.Model):
            marker = models.CharField(max_length=8, default='')

            class Meta:
                app_label = 'model_inheritance'

        class ParentLinkFirst(Parent):
            parent_ptr = models.OneToOneField(
                Parent,
                models.CASCADE,
                parent_link=True,
                related_name='+',
            )
            alt_parent = models.OneToOneField(
                'Parent',
                models.CASCADE,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'

        class ParentLinkLast(Parent):
            alt_parent = models.OneToOneField(
                Parent,
                models.CASCADE,
                related_name='+',
            )
            parent_ptr = models.OneToOneField(
                'Parent',
                models.CASCADE,
                parent_link=True,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'

        for model in (ParentLinkFirst, ParentLinkLast):
            parent_field = model._meta.parents[Parent]
            self.assertTrue(parent_field.remote_field.parent_link)
            self.assertIs(parent_field, model._meta.get_field('parent_ptr'))
            self.assertIs(model._meta.get_field('alt_parent').remote_field.model, Parent)

    @isolate_apps('model_inheritance')
    def test_non_parent_link_on_parent_raises(self):
        class Parent(models.Model):
            class Meta:
                app_label = 'model_inheritance'

        msg = "Add parent_link=True to"
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            class InvalidChild(Parent):
                parent_ptr = models.OneToOneField(
                    Parent,
                    models.CASCADE,
                    related_name='+',
                )

                class Meta:
                    app_label = 'model_inheritance'

    @isolate_apps('model_inheritance')
    def test_parent_link_from_abstract_base_not_overwritten(self):
        class Parent(models.Model):
            class Meta:
                app_label = 'model_inheritance'

        class Other(models.Model):
            class Meta:
                app_label = 'model_inheritance'

        class ParentLinkMixin(models.Model):
            parent_ptr = models.OneToOneField(
                Parent,
                models.CASCADE,
                parent_link=True,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'
                abstract = True

        class Child(ParentLinkMixin, Parent):
            sibling = models.OneToOneField(
                Other,
                models.CASCADE,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'

        parent_field = Child._meta.parents[Parent]
        self.assertTrue(parent_field.remote_field.parent_link)
        self.assertEqual(parent_field.name, 'parent_ptr')

    @isolate_apps('model_inheritance')
    def test_parent_link_overrides_non_parent_mixin_relation(self):
        class Parent(models.Model):
            class Meta:
                app_label = 'model_inheritance'

        class NonParentMixin(models.Model):
            parent_relation = models.OneToOneField(
                Parent,
                models.CASCADE,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'
                abstract = True

        class Child(NonParentMixin, Parent):
            parent_ptr = models.OneToOneField(
                Parent,
                models.CASCADE,
                parent_link=True,
                related_name='+',
            )

            class Meta:
                app_label = 'model_inheritance'

        parent_field = Child._meta.parents[Parent]
        self.assertTrue(parent_field.remote_field.parent_link)
        self.assertEqual(parent_field.name, 'parent_ptr')
