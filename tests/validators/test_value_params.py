from decimal import Decimal

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.validators import KeysValidator
from django.core.exceptions import ValidationError
from django.core.validators import (
    DecimalValidator,
    EmailValidator,
    FileExtensionValidator,
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    ProhibitNullCharactersValidator,
    RegexValidator,
    URLValidator,
    validate_ipv4_address,
    validate_ipv46_address,
    validate_ipv6_address,
)
from django.test import SimpleTestCase


class ValidatorValueParamsTests(SimpleTestCase):
    def _assert_function_validator(self, validator, value, message_template):
        with self.assertRaises(ValidationError) as cm:
            try:
                validator(value)
            except ValidationError as error:
                self.assertIsNotNone(error.params)
                self.assertIn('value', error.params)
                self.assertEqual(error.params['value'], value)
                raise ValidationError(message_template, code=error.code, params=error.params)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, [message_template % {'value': value}])

    def test_regex_validator_includes_value(self):
        validator = RegexValidator(regex=r'^foo$', message='Invalid %(value)s')
        value = 'bar'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, ['Invalid bar'])

    def test_url_validator_includes_value(self):
        validator = URLValidator(message='URL %(value)s is invalid')
        value = 'http://例子.测试/ invalid'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, ['URL http://例子.测试/ invalid is invalid'])

    def test_email_validator_includes_value(self):
        validator = EmailValidator(message='Email %(value)s is invalid')
        value = 'invalid'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, ['Email invalid is invalid'])

    def test_min_value_validator_includes_value(self):
        validator = MinValueValidator(5, message='Too small %(value)s')
        value = 3
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['limit_value'], 5)
        self.assertEqual(params['show_value'], value)
        self.assertEqual(cm.exception.messages, ['Too small 3'])

    def test_max_value_validator_includes_value(self):
        validator = MaxValueValidator(5, message='Too large %(value)s')
        value = 7
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['limit_value'], 5)
        self.assertEqual(params['show_value'], value)
        self.assertEqual(cm.exception.messages, ['Too large 7'])

    def test_min_length_validator_includes_value(self):
        validator = MinLengthValidator(3, message='Too short %(value)s')
        value = 'ab'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['limit_value'], 3)
        self.assertEqual(params['show_value'], len(value))
        self.assertEqual(cm.exception.messages, ['Too short ab'])

    def test_max_length_validator_includes_value(self):
        validator = MaxLengthValidator(3, message='Too long %(value)s')
        value = 'abcd'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['limit_value'], 3)
        self.assertEqual(params['show_value'], len(value))
        self.assertEqual(cm.exception.messages, ['Too long abcd'])

    def test_decimal_validator_max_digits_includes_value(self):
        validator = DecimalValidator(max_digits=4, decimal_places=2)
        validator.messages = {**validator.messages, 'max_digits': 'Too many digits %(value)s'}
        value = Decimal('12345')
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['max'], 4)
        self.assertEqual(cm.exception.messages, ['Too many digits 12345'])

    def test_decimal_validator_max_decimal_places_includes_value(self):
        validator = DecimalValidator(max_digits=6, decimal_places=2)
        validator.messages = {
            **validator.messages,
            'max_decimal_places': 'Too many decimals %(value)s',
        }
        value = Decimal('1.234')
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['max'], 2)
        self.assertEqual(cm.exception.messages, ['Too many decimals 1.234'])

    def test_decimal_validator_max_whole_digits_includes_value(self):
        validator = DecimalValidator(max_digits=5, decimal_places=2)
        validator.messages = {
            **validator.messages,
            'max_whole_digits': 'Too many whole digits %(value)s',
        }
        value = Decimal('1234.5')
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['max'], 3)
        self.assertEqual(cm.exception.messages, ['Too many whole digits 1234.5'])

    def test_file_extension_validator_includes_value(self):
        validator = FileExtensionValidator(
            allowed_extensions=['jpg'],
            message='Disallowed for %(value)s',
        )

        class DummyFile:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        value = DummyFile('photo.txt')
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['extension'], 'txt')
        self.assertEqual(params['allowed_extensions'], 'jpg')
        self.assertEqual(cm.exception.messages, ['Disallowed for photo.txt'])

    def test_prohibit_null_characters_validator_includes_value(self):
        validator = ProhibitNullCharactersValidator(message='Nulls in %(value)s')
        value = 'foo\x00bar'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, ['Nulls in foo\x00bar'])

    def test_keys_validator_missing_keys_includes_value(self):
        validator = KeysValidator(
            keys={'required', 'present'},
            messages={'missing_keys': 'Missing %(keys)s for %(value)s'},
        )
        value = {'present': 1}
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['keys'], 'required')
        self.assertEqual(cm.exception.messages, ["Missing required for {'present': 1}"])

    def test_keys_validator_extra_keys_includes_value(self):
        validator = KeysValidator(
            keys={'expected'},
            strict=True,
            messages={'extra_keys': 'Extra %(keys)s for %(value)s'},
        )
        value = {'expected': 1, 'extra': 2}
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        params = cm.exception.params
        self.assertEqual(params['value'], value)
        self.assertEqual(params['keys'], 'extra')
        self.assertEqual(cm.exception.messages, ["Extra extra for {'expected': 1, 'extra': 2}"])

    def test_username_validator_includes_value(self):
        validator = UnicodeUsernameValidator(message='Invalid username %(value)s')
        value = 'invalid user'
        with self.assertRaises(ValidationError) as cm:
            validator(value)
        self.assertEqual(cm.exception.params['value'], value)
        self.assertEqual(cm.exception.messages, ['Invalid username invalid user'])

    def test_validate_ipv4_address_includes_value(self):
        value = '999.0.0.1'
        self._assert_function_validator(validate_ipv4_address, value, 'IPv4 %(value)s is invalid')

    def test_validate_ipv6_address_includes_value(self):
        value = '::zzz'
        self._assert_function_validator(validate_ipv6_address, value, 'IPv6 %(value)s is invalid')

    def test_validate_ipv46_address_includes_value(self):
        value = 'not-an-ip'
        self._assert_function_validator(validate_ipv46_address, value, 'IP %(value)s is invalid')
