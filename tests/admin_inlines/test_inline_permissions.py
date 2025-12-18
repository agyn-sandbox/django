from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Photo, Report, ReportNoInline, ReportStacked


User = get_user_model()


@override_settings(ROOT_URLCONF='admin_inlines.urls')
class AutoThroughInlinePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.photo1 = Photo.objects.create(name='Alpha')
        cls.photo2 = Photo.objects.create(name='Beta')
        cls.report_ct = ContentType.objects.get_for_model(Report)
        cls.report_stacked_ct = ContentType.objects.get_for_model(
            ReportStacked, for_concrete_model=False
        )
        cls.report_noinline_ct = ContentType.objects.get_for_model(
            ReportNoInline, for_concrete_model=False
        )
        cls.permissions = {
            'add_report': Permission.objects.get(
                content_type=cls.report_ct,
                codename='add_report',
            ),
            'change_report': Permission.objects.get(
                content_type=cls.report_ct,
                codename='change_report',
            ),
            'view_report': Permission.objects.get(
                content_type=cls.report_ct,
                codename='view_report',
            ),
            'view_reportstacked': Permission.objects.get(
                content_type=cls.report_stacked_ct,
                codename='view_reportstacked',
            ),
            'view_reportnoinline': Permission.objects.get(
                content_type=cls.report_noinline_ct,
                codename='view_reportnoinline',
            ),
        }

    def make_user(self, username, perm_keys):
        user = User.objects.create_user(
            username=username,
            email='%s@example.com' % username,
            password='password',
            is_staff=True,
        )
        user.user_permissions.set([self.permissions[key] for key in perm_keys])
        return user

    def _build_inline_post_data(self, formset, parent_data, form_values):
        data = dict(parent_data)
        prefix = formset.prefix
        min_num = formset.min_num or 0
        max_num = formset.max_num if formset.max_num is not None else formset.absolute_max
        base_fields = list(formset.empty_form.fields.keys())
        total_forms = len(form_values)
        data['%s-TOTAL_FORMS' % prefix] = str(total_forms)
        data['%s-INITIAL_FORMS' % prefix] = str(formset.initial_form_count())
        data['%s-MIN_NUM_FORMS' % prefix] = str(min_num)
        data['%s-MAX_NUM_FORMS' % prefix] = str(max_num)
        for index, values in enumerate(form_values):
            for field in base_fields:
                data['%s-%d-%s' % (prefix, index, field)] = values.get(field, '')
        return data

    def _get_inline_formset(self, response):
        inline_admin_formset = response.context['inline_admin_formsets'][0]
        return inline_admin_formset.formset

    def _get_through_instance(self, report, photo):
        return report.photos.through.objects.get(report=report, photo=photo)

    def test_tabular_inline_view_only_readonly(self):
        report = Report.objects.create(name='View Only Tabular')
        report.photos.add(self.photo1)
        user = self.make_user('view_tab', ['view_report'])
        self.client.force_login(user)
        url = reverse('admin:admin_inlines_report_change', args=(report.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = self._get_inline_formset(response)
        self.assertEqual(formset.total_form_count(), formset.initial_form_count())
        self.assertFalse(formset.can_delete)
        self.assertNotContains(response, 'Delete?')
        self.assertNotContains(response, '__prefix__')

        through = self._get_through_instance(report, self.photo1)
        post_data = self._build_inline_post_data(
            formset,
            parent_data={'name': report.name},
            form_values=[{'id': str(through.pk), 'photo': str(self.photo2.pk)}],
        )
        post_data['_save'] = 'Save'
        self.client.post(url, post_data)

        report = Report.objects.get(pk=report.pk)
        self.assertListEqual(list(report.photos.all()), [self.photo1])

    def test_stacked_inline_view_only_readonly(self):
        report = ReportStacked.objects.create(name='View Only Stacked')
        report.photos.add(self.photo1)
        user = self.make_user('view_stack', ['view_reportstacked'])
        self.client.force_login(user)
        url = reverse('admin:admin_inlines_reportstacked_change', args=(report.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = self._get_inline_formset(response)
        self.assertEqual(formset.total_form_count(), formset.initial_form_count())
        self.assertFalse(formset.can_delete)
        self.assertNotContains(response, 'Delete?')
        self.assertNotContains(response, '__prefix__')

        through = self._get_through_instance(report, self.photo1)
        post_data = self._build_inline_post_data(
            formset,
            parent_data={'name': report.name},
            form_values=[{'id': str(through.pk), 'photo': str(self.photo2.pk)}],
        )
        post_data['_save'] = 'Save'
        self.client.post(url, post_data)

        refreshed = ReportStacked.objects.get(pk=report.pk)
        self.assertListEqual(list(refreshed.photos.all()), [self.photo1])

    def test_view_only_many_to_many_field_without_inline_is_readonly(self):
        report = ReportNoInline.objects.create(name='View Only No Inline')
        report.photos.add(self.photo1)
        user = self.make_user('view_no_inline', ['view_reportnoinline'])
        self.client.force_login(user)
        url = reverse('admin:admin_inlines_reportnoinline_change', args=(report.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        admin_form = response.context['adminform']
        self.assertIn('photos', admin_form.readonly_fields)
        self.assertNotIn('photos', admin_form.form.fields)

    def test_change_only_user_can_edit_inline_on_change_view(self):
        report = Report.objects.create(name='Change Only Report')
        report.photos.add(self.photo1)
        user = self.make_user('change_only', ['view_report', 'change_report'])
        self.client.force_login(user)
        url = reverse('admin:admin_inlines_report_change', args=(report.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = self._get_inline_formset(response)
        through = self._get_through_instance(report, self.photo1)
        post_data = self._build_inline_post_data(
            formset,
            parent_data={'name': report.name},
            form_values=[
                {'id': str(through.pk), 'photo': str(self.photo1.pk)},
                {'id': '', 'photo': str(self.photo2.pk)},
            ],
        )
        post_data['_save'] = 'Save'
        post_response = self.client.post(url, post_data)
        self.assertEqual(post_response.status_code, 302)

        report = Report.objects.get(pk=report.pk)
        self.assertCountEqual(report.photos.values_list('pk', flat=True), [self.photo1.pk, self.photo2.pk])

    def test_add_only_user_inline_permissions(self):
        user = self.make_user('add_only', ['add_report', 'view_report'])
        self.client.force_login(user)

        add_url = reverse('admin:admin_inlines_report_add')
        add_response = self.client.get(add_url)
        self.assertEqual(add_response.status_code, 200)
        add_formset = self._get_inline_formset(add_response)
        self.assertGreater(add_formset.total_form_count(), 0)

        form_values = [{'id': '', 'photo': str(self.photo1.pk)}]
        form_values.extend({'id': '', 'photo': ''} for _ in range(add_formset.total_form_count() - 1))
        post_data = self._build_inline_post_data(
            add_formset,
            parent_data={'name': 'Add Only Created'},
            form_values=form_values,
        )
        post_data['_save'] = 'Save'
        add_post_response = self.client.post(add_url, post_data)
        self.assertEqual(add_post_response.status_code, 302)

        created_report = Report.objects.get(name='Add Only Created')
        self.assertListEqual(list(created_report.photos.all()), [self.photo1])

        change_url = reverse('admin:admin_inlines_report_change', args=(created_report.pk,))
        change_response = self.client.get(change_url)
        self.assertEqual(change_response.status_code, 200)
        change_formset = self._get_inline_formset(change_response)
        self.assertEqual(change_formset.total_form_count(), change_formset.initial_form_count())
        self.assertFalse(change_formset.can_delete)
        self.assertNotContains(change_response, '__prefix__')

        through = self._get_through_instance(created_report, self.photo1)
        change_post_data = self._build_inline_post_data(
            change_formset,
            parent_data={'name': created_report.name},
            form_values=[{'id': str(through.pk), 'photo': str(self.photo2.pk)}],
        )
        change_post_data['_save'] = 'Save'
        self.client.post(change_url, change_post_data)

        created_report = Report.objects.get(pk=created_report.pk)
        self.assertListEqual(list(created_report.photos.all()), [self.photo1])
