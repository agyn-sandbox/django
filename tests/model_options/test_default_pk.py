from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import SimpleTestCase, override_settings
from django.test.utils import isolate_apps
from model_options.fields import MyBigAutoField, MySmallAutoField


@isolate_apps('model_options')
class TestDefaultPK(SimpleTestCase):
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.NonexistentAutoField')
    def test_default_auto_field_setting_nonexistent(self):
        msg = (
            "DEFAULT_AUTO_FIELD refers to the module "
            "'django.db.models.NonexistentAutoField' that could not be "
            "imported."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            class Model(models.Model):
                pass

    @isolate_apps('model_options.apps.ModelPKNonexistentConfig')
    def test_app_default_auto_field_nonexistent(self):
        msg = (
            "model_options.apps.ModelPKNonexistentConfig.default_auto_field "
            "refers to the module 'django.db.models.NonexistentAutoField' "
            "that could not be imported."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            class Model(models.Model):
                pass

    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.TextField')
    def test_default_auto_field_setting_non_auto(self):
        msg = (
            "Primary key 'django.db.models.TextField' referred by "
            "DEFAULT_AUTO_FIELD must subclass AutoField."
        )
        with self.assertRaisesMessage(ValueError, msg):
            class Model(models.Model):
                pass

    @isolate_apps('model_options.apps.ModelPKNonAutoConfig')
    def test_app_default_auto_field_non_auto(self):
        msg = (
            "Primary key 'django.db.models.TextField' referred by "
            "model_options.apps.ModelPKNonAutoConfig.default_auto_field must "
            "subclass AutoField."
        )
        with self.assertRaisesMessage(ValueError, msg):
            class Model(models.Model):
                pass

    @override_settings(DEFAULT_AUTO_FIELD=None)
    def test_default_auto_field_setting_none(self):
        msg = 'DEFAULT_AUTO_FIELD must not be empty.'
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            class Model(models.Model):
                pass

    @isolate_apps('model_options.apps.ModelPKNoneConfig')
    def test_app_default_auto_field_none(self):
        msg = (
            'model_options.apps.ModelPKNoneConfig.default_auto_field must not '
            'be empty.'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            class Model(models.Model):
                pass

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.SmallAutoField')
    def test_default_auto_field_setting(self):
        class Model(models.Model):
            pass

        self.assertIsInstance(Model._meta.pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='model_options.fields.MyBigAutoField')
    def test_default_auto_field_setting_custom_big_subclass(self):
        class Model(models.Model):
            pass

        pk = Model._meta.pk
        self.assertIsInstance(pk, MyBigAutoField)
        self.assertIsInstance(pk, models.BigAutoField)

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='model_options.fields.MySmallAutoField')
    def test_default_auto_field_setting_custom_small_subclass(self):
        class Model(models.Model):
            pass

        pk = Model._meta.pk
        self.assertIsInstance(pk, MySmallAutoField)
        self.assertIsInstance(pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_app_default_auto_field(self):
        class Model(models.Model):
            pass

        self.assertIsInstance(Model._meta.pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelPKCustomBigConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_app_default_auto_field_custom_big_subclass(self):
        class Model(models.Model):
            pass

        pk = Model._meta.pk
        self.assertIsInstance(pk, MyBigAutoField)
        self.assertIsInstance(pk, models.BigAutoField)

    @isolate_apps('model_options.apps.ModelPKCustomSmallConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_app_default_auto_field_custom_small_subclass(self):
        class Model(models.Model):
            pass

        pk = Model._meta.pk
        self.assertIsInstance(pk, MySmallAutoField)
        self.assertIsInstance(pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.SmallAutoField')
    def test_m2m_default_auto_field_setting(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_m2m_app_default_auto_field(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='model_options.fields.MyBigAutoField')
    def test_m2m_default_auto_field_setting_custom_big_subclass(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, MyBigAutoField)
        self.assertIsInstance(m2m_pk, models.BigAutoField)

    @isolate_apps('model_options.apps.ModelDefaultPKConfig')
    @override_settings(DEFAULT_AUTO_FIELD='model_options.fields.MySmallAutoField')
    def test_m2m_default_auto_field_setting_custom_small_subclass(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, MySmallAutoField)
        self.assertIsInstance(m2m_pk, models.SmallAutoField)

    @isolate_apps('model_options.apps.ModelPKCustomBigConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_m2m_app_default_auto_field_custom_big_subclass(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, MyBigAutoField)
        self.assertIsInstance(m2m_pk, models.BigAutoField)

    @isolate_apps('model_options.apps.ModelPKCustomSmallConfig')
    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    def test_m2m_app_default_auto_field_custom_small_subclass(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField('self')

        m2m_pk = M2MModel._meta.get_field('m2m').remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, MySmallAutoField)
        self.assertIsInstance(m2m_pk, models.SmallAutoField)
