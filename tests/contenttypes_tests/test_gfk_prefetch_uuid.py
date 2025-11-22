from django.test import TestCase

from .models import UUIDBar, UUIDFoo


class GenericForeignKeyPrefetchTests(TestCase):

    def test_forward_gfk_prefetch_raises_error(self):
        foo = UUIDFoo.objects.create()
        bar = UUIDBar()
        bar.foo = foo
        bar.save()

        message = (
            "prefetch_related() does not support forward GenericForeignKey on this Django version. "
            "Use a GenericRelation on the reverse side or upgrade to Django 5.0+ and use GenericPrefetch."
        )
        with self.assertRaisesMessage(ValueError, message):
            list(UUIDBar.objects.prefetch_related('foo'))

    def test_reverse_genericrelation_prefetch_ok(self):
        foo = UUIDFoo.objects.create()
        bar = UUIDBar()
        bar.foo = foo
        bar.save()

        qs = UUIDFoo.objects.prefetch_related('bars')
        with self.assertNumQueries(2):
            foos = list(qs)

        with self.assertNumQueries(0):
            self.assertEqual(list(foos[0].bars.all()), [bar])
