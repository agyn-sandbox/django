from django.db.models import Value
from django.test import SimpleTestCase


class ValueResolveOutputFieldTests(SimpleTestCase):
    def test_value_resolves_charfield_without_max_length_validator(self):
        """
        Value._resolve_output_field() should return a CharField without attaching
        a MaxLengthValidator when no max_length is provided. Previously a
        MaxLengthValidator(None) was added which caused TypeError during clean().
        """
        x = Value('test')
        y = x._resolve_output_field()

        # Ensure no MaxLengthValidator is attached when max_length is None.
        self.assertFalse(
            any(v.__class__.__name__ == 'MaxLengthValidator' for v in y.validators)
        )

        # This should not raise (it used to crash with TypeError in compare()).
        y.clean('1', model_instance=None)
