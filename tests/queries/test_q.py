from django.db.models import Exists, F, OuterRef, Q, Value
from django.test import SimpleTestCase

from .models import Author


class QTests(SimpleTestCase):
    def test_combine_and_empty(self):
        q = Q(x=1)
        self.assertEqual(q & Q(), q)
        self.assertEqual(Q() & q, q)

        q = Q(x__in={}.keys())
        self.assertEqual(q & Q(), q)
        self.assertEqual(Q() & q, q)

    def test_combine_and_both_empty(self):
        self.assertEqual(Q() & Q(), Q())

    def test_combine_or_empty(self):
        q = Q(x=1)
        self.assertEqual(q | Q(), q)
        self.assertEqual(Q() | q, q)

        q = Q(x__in={}.keys())
        self.assertEqual(q | Q(), q)
        self.assertEqual(Q() | q, q)

    def test_combine_or_both_empty(self):
        self.assertEqual(Q() | Q(), Q())

    def test_combine_not_q_object(self):
        obj = object()
        q = Q(x=1)
        with self.assertRaisesMessage(TypeError, str(obj)):
            q | obj
        with self.assertRaisesMessage(TypeError, str(obj)):
            q & obj

    def test_deconstruct(self):
        q = Q(price__gt=F('discounted_price'))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(path, 'django.db.models.Q')
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {'price__gt': F('discounted_price')})

    def test_deconstruct_negated(self):
        q = ~Q(price__gt=F('discounted_price'))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {
            'price__gt': F('discounted_price'),
            '_negated': True,
        })

    def test_deconstruct_or(self):
        q1 = Q(price__gt=F('discounted_price'))
        q2 = Q(price=F('discounted_price'))
        q = q1 | q2
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, (
            ('price__gt', F('discounted_price')),
            ('price', F('discounted_price')),
        ))
        self.assertEqual(kwargs, {'_connector': 'OR'})

    def test_deconstruct_and(self):
        q1 = Q(price__gt=F('discounted_price'))
        q2 = Q(price=F('discounted_price'))
        q = q1 & q2
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, (
            ('price__gt', F('discounted_price')),
            ('price', F('discounted_price')),
        ))
        self.assertEqual(kwargs, {})

    def test_deconstruct_multiple_kwargs(self):
        q = Q(price__gt=F('discounted_price'), price=F('discounted_price'))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, (
            ('price', F('discounted_price')),
            ('price__gt', F('discounted_price')),
        ))
        self.assertEqual(kwargs, {})

    def test_deconstruct_nested(self):
        q = Q(Q(price__gt=F('discounted_price')))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, (Q(price__gt=F('discounted_price')),))
        self.assertEqual(kwargs, {})

    def test_deconstruct_exists_child(self):
        exists = Exists(Author.objects.filter(pk=OuterRef('pk')))
        q = Q(exists)
        path, args, kwargs = q.deconstruct()
        self.assertEqual(path, 'django.db.models.Q')
        self.assertEqual(args, (exists,))
        self.assertEqual(kwargs, {})

    def test_deconstruct_boolean_literal_child(self):
        q = Q(False)
        path, args, kwargs = q.deconstruct()
        self.assertEqual(path, 'django.db.models.Q')
        self.assertEqual(args, (False,))
        self.assertEqual(kwargs, {})

    def test_boolean_literals_combination(self):
        and_q = Q(x=1) & True
        path, args, kwargs = and_q.deconstruct()
        self.assertEqual(args[0], ('x', 1))
        self.assertIsInstance(args[1], Value)
        self.assertTrue(args[1].value)
        self.assertEqual(kwargs, {})

        or_q = Q(x=1) | False
        path, args, kwargs = or_q.deconstruct()
        self.assertEqual(args[0], ('x', 1))
        self.assertIsInstance(args[1], Value)
        self.assertFalse(args[1].value)
        self.assertEqual(kwargs, {'_connector': 'OR'})

    def test_boolean_literals_combination_empty_self(self):
        and_q = Q() & True
        self.assertIsInstance(and_q, Value)
        self.assertTrue(and_q.value)

        or_q = Q() | False
        self.assertIsInstance(or_q, Value)
        self.assertFalse(or_q.value)

    def test_reconstruct(self):
        q = Q(price__gt=F('discounted_price'))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(Q(*args, **kwargs), q)

    def test_reconstruct_negated(self):
        q = ~Q(price__gt=F('discounted_price'))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(Q(*args, **kwargs), q)

    def test_reconstruct_or(self):
        q1 = Q(price__gt=F('discounted_price'))
        q2 = Q(price=F('discounted_price'))
        q = q1 | q2
        path, args, kwargs = q.deconstruct()
        self.assertEqual(Q(*args, **kwargs), q)

    def test_reconstruct_and(self):
        q1 = Q(price__gt=F('discounted_price'))
        q2 = Q(price=F('discounted_price'))
        q = q1 & q2
        path, args, kwargs = q.deconstruct()
        self.assertEqual(Q(*args, **kwargs), q)

    def test_lookup_tuple_deconstruct_parity(self):
        tuple_path, tuple_args, tuple_kwargs = Q(('x', 1)).deconstruct()
        kw_path, kw_args, kw_kwargs = Q(x=1).deconstruct()
        self.assertEqual(tuple_path, kw_path)
        self.assertEqual(tuple_args, kw_args)
        self.assertEqual(tuple_kwargs, kw_kwargs)

    def test_conditional_expression_combinations(self):
        exists = Exists(Author.objects.filter(pk=OuterRef('pk')))
        or_q = Q(x=1) | exists
        path, args, kwargs = or_q.deconstruct()
        self.assertEqual(args, (('x', 1), exists))
        self.assertEqual(kwargs, {'_connector': 'OR'})

        value_true = Value(True)
        and_q = Q(x=1) & value_true
        path, args, kwargs = and_q.deconstruct()
        self.assertEqual(args, (('x', 1), value_true))
        self.assertEqual(kwargs, {})

    def test_conditional_expression_combination_empty_self(self):
        exists = Exists(Author.objects.filter(pk=OuterRef('pk')))
        and_combined = Q() & exists
        self.assertIsInstance(and_combined, Exists)
        self.assertIsNot(and_combined, exists)
        self.assertEqual(and_combined.negated, exists.negated)

        or_combined = Q() | exists
        self.assertIsInstance(or_combined, Exists)
        self.assertIsNot(or_combined, exists)
        self.assertEqual(or_combined.negated, exists.negated)
