from django.core.exceptions import ValidationError
from django.forms import ChoiceField, ModelChoiceField, ModelMultipleChoiceField
from django.test import TestCase

from ..models import ChoiceModel


class ModelChoiceFieldTests(TestCase):

    def test_modelchoicefield_invalid_choice_includes_value_in_message_and_params(self):
        ChoiceModel.objects.create(pk=1, name='alpha')
        field = ModelChoiceField(queryset=ChoiceModel.objects.all())
        invalid_value = '2'

        with self.assertRaises(ValidationError) as cm:
            field.clean(invalid_value)

        self.assertEqual(
            cm.exception.messages,
            ['Select a valid choice. 2 is not one of the available choices.'],
        )
        self.assertEqual(cm.exception.error_list[0].code, 'invalid_choice')
        self.assertEqual(cm.exception.error_list[0].params['value'], invalid_value)

    def test_parity_with_choicefield_invalid_choice_message(self):
        ChoiceModel.objects.create(pk=1, name='alpha')
        choice_field = ChoiceField(choices=[('1', 'alpha')])
        model_field = ModelChoiceField(queryset=ChoiceModel.objects.all())
        invalid_value = '2'

        with self.assertRaises(ValidationError) as model_exc:
            model_field.clean(invalid_value)

        with self.assertRaises(ValidationError) as choice_exc:
            choice_field.clean(invalid_value)

        self.assertEqual(model_exc.exception.messages, choice_exc.exception.messages)

    def test_modelmultiplechoicefield_invalid_choice_still_includes_value(self):
        ChoiceModel.objects.create(pk=1, name='alpha')
        field = ModelMultipleChoiceField(queryset=ChoiceModel.objects.all())
        invalid_value = '2'

        with self.assertRaises(ValidationError) as cm:
            field.clean([invalid_value])

        self.assertEqual(
            cm.exception.messages,
            ['Select a valid choice. 2 is not one of the available choices.'],
        )
        self.assertEqual(cm.exception.error_list[0].code, 'invalid_choice')
        self.assertEqual(cm.exception.error_list[0].params['value'], invalid_value)
