from django.contrib.auth import get_user_model
from django.test import TestCase
from cards.models import EmployeeCard
from cards.services.vcard import build_vcard


class CompanyWebsiteTests(TestCase):
    def test_all_cards_and_exports_use_company_website_even_with_legacy_values(self):
        for previous in ['', 'https://old.example.com']:
            with self.subTest(previous=previous):
                card = EmployeeCard.objects.create(full_name='Иван Иванов', website=previous, is_active=True)
                response = self.client.get(card.get_absolute_url())
                self.assertContains(response, 'href="https://www.kmzlift.ru"')
                self.assertNotContains(response, 'old.example.com')
                data = build_vcard(card).replace(b'\r\n ', b'').decode()
                self.assertIn('URL:https://www.kmzlift.ru\r\n', data)
                self.assertNotIn('old.example.com', data)

    def test_admin_shows_constant_and_cannot_override_it_with_form_submission(self):
        user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'Test-password-12345')
        self.client.force_login(user)
        card = EmployeeCard.objects.create(full_name='Иван Иванов', is_active=True)
        url = f'/manage/cards/employeecard/{card.pk}/change/'
        page = self.client.get(url)
        self.assertContains(page, 'https://www.kmzlift.ru')
        self.assertNotContains(page, 'name="website"')
        result = self.client.post(url, {'full_name': 'Иван Иванов', 'is_active': 'on',
            'website': 'https://wrong.example.com', 'company_website': 'https://wrong.example.com'})
        self.assertEqual(result.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.website, '')
        self.assertContains(self.client.get(card.get_absolute_url()), 'href="https://www.kmzlift.ru"')
