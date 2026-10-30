from django.test import TestCase
from cards.forms import EmployeeCardForm


class PhoneFormatTests(TestCase):
    def test_both_phone_fields_save_in_the_same_format(self):
        for raw, expected in [('+74951234567', '+7 (495) 123-45-67'),
                              ('8 (495) 123 45 67', '+7 (495) 123-45-67'),
                              ('9001234567', '+7 (900) 123-45-67'),
                              ('+7 (900) 123-45-67', '+7 (900) 123-45-67')]:
            with self.subTest(raw=raw):
                form = EmployeeCardForm(data={'full_name': 'Иван Иванов', 'phone': raw, 'mobile_phone': raw})
                self.assertTrue(form.is_valid(), form.errors)
                card = form.save()
                self.assertEqual(card.phone, expected)
                self.assertEqual(card.mobile_phone, expected)

    def test_incomplete_or_extra_digits_are_rejected_for_both_fields(self):
        for raw in ['123', '+7 900 123 45', '+7 900 123 45 678', '+7abc9001234567', '----']:
            for field in ['phone', 'mobile_phone']:
                with self.subTest(raw=raw, field=field):
                    form = EmployeeCardForm(data={'full_name': 'Иван', field: raw})
                    self.assertFalse(form.is_valid())
                    self.assertIn(field, form.errors)

    def test_optional_numbers_and_extension_leading_zero_are_preserved(self):
        form = EmployeeCardForm(data={'full_name': 'Иван'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().phone, '')
        form = EmployeeCardForm(data={'full_name': 'Иван', 'phone': '84951234567', 'phone_extension': '0123'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().phone_extension, '0123')
