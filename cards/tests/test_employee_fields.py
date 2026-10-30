from django.contrib.auth import get_user_model
from django.test import TestCase
from cards.forms import EmployeeCardForm
from cards.models import EmployeeCard
from cards.services.vcard import build_vcard


class EmployeeFieldTests(TestCase):
    values = {
        'full_name': 'Иванов Александр Сергеевич', 'job_title': 'Главный инженер',
        'department': 'Отдел технического сопровождения', 'phone': '+7 (495) 000-00-00',
        'phone_extension': '0123', 'mobile_phone': '+7 (900) 000-00-00',
        'website': 'https://company.example.com', 'is_active': True,
    }

    def test_admin_saves_all_requested_fields_without_changing_card_address(self):
        user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'Test-password-long123')
        self.client.force_login(user)
        card = EmployeeCard.objects.create(full_name='Иванов Александр')
        response = self.client.post(f'/manage/cards/employeecard/{card.pk}/change/', self.values)
        self.assertEqual(response.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.full_name, 'Иванов Александр Сергеевич')
        self.assertEqual(card.department, 'Отдел технического сопровождения')
        self.assertEqual(card.phone_extension, '0123')
        self.assertEqual(card.mobile_phone, '+7 (900) 000-00-00')
        self.assertEqual(card.website, 'https://company.example.com')
        self.assertEqual(card.get_absolute_url(), f'/c/{card.pk}/')

    def test_card_shows_department_separate_phones_extension_and_kmz_site(self):
        form = EmployeeCardForm(data=self.values)
        self.assertTrue(form.is_valid(), form.errors)
        card = form.save()
        response = self.client.get(card.get_absolute_url())
        for text in ['Иванов Александр Сергеевич', 'Отдел технического сопровождения',
                     'Рабочий телефон', 'доб. 0123', 'Мобильный телефон', 'Сайт КМЗ']:
            self.assertContains(response, text)
        self.assertContains(response, 'href="tel:+74950000000;ext=0123"')
        self.assertContains(response, 'href="tel:+79000000000"')
        self.assertContains(response, 'href="https://company.example.com"')

    def test_rejects_invalid_extension_mobile_and_extension_without_work_number(self):
        for update, field in [({'phone_extension': '12;ext=99'}, 'phone_extension'),
                              ({'phone_extension': '1\n2'}, 'phone_extension'),
                              ({'phone_extension': '12345678901'}, 'phone_extension'),
                              ({'phone': '', 'phone_extension': '123'}, 'phone_extension'),
                              ({'mobile_phone': 'call-me'}, 'mobile_phone')]:
            with self.subTest(update=update):
                form = EmployeeCardForm(data={**self.values, **update})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_vcard_exports_department_both_numbers_site_and_extension_note(self):
        form = EmployeeCardForm(data=self.values)
        self.assertTrue(form.is_valid(), form.errors)
        card = form.save()
        data = build_vcard(card).replace(b'\r\n ', b'').decode()
        self.assertIn('FN:Иванов Александр Сергеевич\r\n', data)
        self.assertIn('ORG:Карачаровский механический завод;Отдел технического сопровождения\r\n', data)
        self.assertIn('TEL;TYPE=WORK,VOICE:+74950000000\r\n', data)
        self.assertIn('TEL;TYPE=CELL,VOICE:+79000000000\r\n', data)
        self.assertIn('Добавочный рабочего телефона: 0123', data)
        self.assertIn('URL:https://company.example.com\r\n', data)

    def test_absent_fields_stay_hidden_for_existing_cards(self):
        card = EmployeeCard.objects.create(full_name='Иванов Александр Сергеевич', is_active=True)
        response = self.client.get(card.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'доб.')
        self.assertNotContains(response, 'Мобильный телефон')
        self.assertNotContains(response, 'Сайт КМЗ')
