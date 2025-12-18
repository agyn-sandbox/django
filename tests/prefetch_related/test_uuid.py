import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps

from .models import Flea, House, Person, Pet, Room


class UUIDPrefetchRelated(TestCase):

    def test_prefetch_related_from_uuid_model(self):
        Pet.objects.create(name='Fifi').people.add(
            Person.objects.create(name='Ellen'),
            Person.objects.create(name='George'),
        )

        with self.assertNumQueries(2):
            pet = Pet.objects.prefetch_related('people').get(name='Fifi')
        with self.assertNumQueries(0):
            self.assertEqual(2, len(pet.people.all()))

    def test_prefetch_related_to_uuid_model(self):
        Person.objects.create(name='Bella').pets.add(
            Pet.objects.create(name='Socks'),
            Pet.objects.create(name='Coffee'),
        )

        with self.assertNumQueries(2):
            person = Person.objects.prefetch_related('pets').get(name='Bella')
        with self.assertNumQueries(0):
            self.assertEqual(2, len(person.pets.all()))

    def test_prefetch_related_from_uuid_model_to_uuid_model(self):
        fleas = [Flea.objects.create() for i in range(3)]
        Pet.objects.create(name='Fifi').fleas_hosted.add(*fleas)
        Pet.objects.create(name='Bobo').fleas_hosted.add(*fleas)

        with self.assertNumQueries(2):
            pet = Pet.objects.prefetch_related('fleas_hosted').get(name='Fifi')
        with self.assertNumQueries(0):
            self.assertEqual(3, len(pet.fleas_hosted.all()))

        with self.assertNumQueries(2):
            flea = Flea.objects.prefetch_related('pets_visited').get(pk=fleas[0].pk)
        with self.assertNumQueries(0):
            self.assertEqual(2, len(flea.pets_visited.all()))

    def test_prefetch_related_from_uuid_model_to_uuid_model_with_values_flat(self):
        pet = Pet.objects.create(name='Fifi')
        pet.people.add(
            Person.objects.create(name='Ellen'),
            Person.objects.create(name='George'),
        )
        self.assertSequenceEqual(
            Pet.objects.prefetch_related('fleas_hosted').values_list('id', flat=True),
            [pet.id]
        )


class UUIDPrefetchRelatedLookups(TestCase):

    @classmethod
    def setUpTestData(cls):
        house = House.objects.create(name='Redwood', address='Arcata')
        room = Room.objects.create(name='Racoon', house=house)
        fleas = [Flea.objects.create(current_room=room) for i in range(3)]
        pet = Pet.objects.create(name='Spooky')
        pet.fleas_hosted.add(*fleas)
        person = Person.objects.create(name='Bob')
        person.houses.add(house)
        person.pets.add(pet)
        person.fleas_hosted.add(*fleas)

    def test_from_uuid_pk_lookup_uuid_pk_integer_pk(self):
        # From uuid-pk model, prefetch <uuid-pk model>.<integer-pk model>:
        with self.assertNumQueries(4):
            spooky = Pet.objects.prefetch_related('fleas_hosted__current_room__house').get(name='Spooky')
        with self.assertNumQueries(0):
            self.assertEqual('Racoon', spooky.fleas_hosted.all()[0].current_room.name)

    def test_from_uuid_pk_lookup_integer_pk2_uuid_pk2(self):
        # From uuid-pk model, prefetch <integer-pk model>.<integer-pk model>.<uuid-pk model>.<uuid-pk model>:
        with self.assertNumQueries(5):
            spooky = Pet.objects.prefetch_related('people__houses__rooms__fleas').get(name='Spooky')
        with self.assertNumQueries(0):
            self.assertEqual(3, len(spooky.people.all()[0].houses.all()[0].rooms.all()[0].fleas.all()))

    def test_from_integer_pk_lookup_uuid_pk_integer_pk(self):
        # From integer-pk model, prefetch <uuid-pk model>.<integer-pk model>:
        with self.assertNumQueries(3):
            racoon = Room.objects.prefetch_related('fleas__people_visited').get(name='Racoon')
        with self.assertNumQueries(0):
            self.assertEqual('Bob', racoon.fleas.all()[0].people_visited.all()[0].name)

    def test_from_integer_pk_lookup_integer_pk_uuid_pk(self):
        # From integer-pk model, prefetch <integer-pk model>.<uuid-pk model>:
        with self.assertNumQueries(3):
            redwood = House.objects.prefetch_related('rooms__fleas').get(name='Redwood')
        with self.assertNumQueries(0):
            self.assertEqual(3, len(redwood.rooms.all()[0].fleas.all()))

    def test_from_integer_pk_lookup_integer_pk_uuid_pk_uuid_pk(self):
        # From integer-pk model, prefetch <integer-pk model>.<uuid-pk model>.<uuid-pk model>:
        with self.assertNumQueries(4):
            redwood = House.objects.prefetch_related('rooms__fleas__pets_visited').get(name='Redwood')
        with self.assertNumQueries(0):
            self.assertEqual('Spooky', redwood.rooms.all()[0].fleas.all()[0].pets_visited.all()[0].name)


@isolate_apps('prefetch_related')
class GenericForeignKeyUUIDPrefetchTests(TestCase):

    class Foo(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

        class Meta:
            app_label = 'prefetch_related'

    class Bar(models.Model):
        foo_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        foo_object_id = models.CharField(max_length=255, db_index=True)
        foo = GenericForeignKey('foo_content_type', 'foo_object_id')

        class Meta:
            app_label = 'prefetch_related'

    def test_prefetch_related_generic_foreign_key_hyphenated_uuid(self):
        foo_id = uuid.uuid4()
        foo = self.Foo.objects.create(id=foo_id)
        self.Bar.objects.create(
            foo_content_type=ContentType.objects.get_for_model(self.Foo),
            foo_object_id=str(foo_id),
        )

        bar = self.Bar.objects.get()
        self.assertEqual(foo.pk, bar.foo.pk)

        foo_field = next(field for field in self.Bar._meta.private_fields if field.name == 'foo')
        rel_qs, rel_key, instance_key, *_ = foo_field.get_prefetch_queryset([bar])
        self.assertIn(instance_key(bar), {rel_key(obj) for obj in rel_qs})

        bars = list(self.Bar.objects.all().prefetch_related('foo'))

        self.assertIsNotNone(bars[0].foo)
        self.assertEqual(foo.pk, bars[0].foo.pk)

    def test_prefetch_related_generic_foreign_key_hex_uuid(self):
        foo_id = uuid.uuid4()
        foo = self.Foo.objects.create(id=foo_id)
        self.Bar.objects.create(
            foo_content_type=ContentType.objects.get_for_model(self.Foo),
            foo_object_id=foo_id.hex,
        )

        bar = self.Bar.objects.get()
        self.assertEqual(foo.pk, bar.foo.pk)

        foo_field = next(field for field in self.Bar._meta.private_fields if field.name == 'foo')
        rel_qs, rel_key, instance_key, *_ = foo_field.get_prefetch_queryset([bar])
        self.assertIn(instance_key(bar), {rel_key(obj) for obj in rel_qs})

        bars = list(self.Bar.objects.all().prefetch_related('foo'))

        self.assertIsNotNone(bars[0].foo)
        self.assertEqual(foo.pk, bars[0].foo.pk)
