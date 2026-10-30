from io import BytesIO
import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from cards.models import EmployeeCard
from cards.forms import EmployeeCardForm


class AdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'Test-only-long-password')

    def test_anonymous_cannot_create_or_edit(self):
        card = EmployeeCard.objects.create(full_name='Иван Иванов')
        for url in ['/manage/cards/employeecard/add/', f'/manage/cards/employeecard/{card.pk}/change/']:
            response = self.client.post(url, {'full_name': 'Подмена'})
            self.assertEqual(response.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.full_name, 'Иван Иванов')
        self.assertEqual(EmployeeCard.objects.count(), 1)

    def test_administrator_creates_edits_and_disables_without_changing_id(self):
        self.client.force_login(self.user)
        response = self.client.post('/manage/cards/employeecard/add/', {
            'full_name': 'Иван Иванов', 'job_title': 'Инженер', 'is_active': 'on', '_save': 'Сохранить'})
        self.assertEqual(response.status_code, 302)
        card = EmployeeCard.objects.get()
        old_id, old_url = card.pk, card.get_absolute_url()
        response = self.client.post(f'/manage/cards/employeecard/{card.pk}/change/', {
            'full_name': 'Пётр Петров', 'job_title': 'Руководитель', '_save': 'Сохранить'})
        self.assertEqual(response.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.pk, old_id)
        self.assertEqual(card.get_absolute_url(), old_url)
        self.assertEqual(card.full_name, 'Пётр Петров')
        self.assertFalse(card.is_active)

    def test_admin_cannot_delete_card_and_recycle_identity(self):
        self.client.force_login(self.user)
        card = EmployeeCard.objects.create(full_name='Иван')
        self.assertEqual(self.client.post(f'/manage/cards/employeecard/{card.pk}/delete/', {'post': 'yes'}).status_code, 403)
        self.assertTrue(EmployeeCard.objects.filter(pk=card.pk).exists())

    def test_staff_without_card_permissions_cannot_edit(self):
        user = get_user_model().objects.create_user('staff', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/manage/cards/employeecard/add/').status_code, 403)

    def test_view_only_staff_cannot_disable_cards_using_bulk_action(self):
        user = get_user_model().objects.create_user('viewer', is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename='view_employeecard'))
        self.client.force_login(user)
        card = EmployeeCard.objects.create(full_name='Иван', is_active=True)
        self.client.post('/manage/cards/employeecard/', {
            'action': 'disable_cards', '_selected_action': str(card.pk), 'index': '0'})
        card.refresh_from_db()
        self.assertTrue(card.is_active)

    def test_admin_change_page_and_preview_links_render(self):
        self.client.force_login(self.user)
        card = EmployeeCard.objects.create(full_name='Иван', is_active=True)
        response = self.client.get(f'/manage/cards/employeecard/{card.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'qr.svg')
        self.assertContains(response, f'/manage/preview/{card.pk}/')


class FormTests(TestCase):
    def test_rejects_blank_name_invalid_email_and_unsafe_links(self):
        for values, field in [({'full_name': '  '}, 'full_name'),
                              ({'full_name': 'Иван', 'email': 'bad'}, 'email'),
                              ({'full_name': 'Иван', 'messenger_url': 'javascript:alert(1)'}, 'messenger_url'),
                              ({'full_name': 'Иван', 'messenger_url': 'ftp://example.com'}, 'messenger_url'),
                              ({'full_name': 'Иван', 'phone': '123;ext=9'}, 'phone')]:
            with self.subTest(field=field):
                form = EmployeeCardForm(data=values)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_rejects_html_disguised_as_photo(self):
        form = EmployeeCardForm(data={'full_name': 'Иван'}, files={
            'photo': SimpleUploadedFile('face.jpg', b'<html>bad</html>', 'image/jpeg')})
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_photo_reencoded_without_exif_or_original_filename(self):
        out = BytesIO()
        img = Image.new('RGB', (50, 50), 'white')
        exif = Image.Exif(); exif[0x010E] = 'private metadata'
        img.save(out, 'JPEG', exif=exif)
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            form = EmployeeCardForm(data={'full_name': 'Иван'}, files={
                'photo': SimpleUploadedFile('private-employee.jpg', out.getvalue(), 'image/jpeg')})
            self.assertTrue(form.is_valid(), form.errors)
            card = form.save()
            self.assertNotIn('private-employee', card.photo.name)
            with Image.open(card.photo.path) as stored:
                self.assertEqual(dict(stored.getexif()), {})

    def test_rejects_photo_larger_than_five_mb(self):
        out = BytesIO(); Image.new('RGB', (1, 1)).save(out, 'PNG')
        form = EmployeeCardForm(data={'full_name': 'Иван'}, files={
            'photo': SimpleUploadedFile('big.png', out.getvalue()+b'0'*(5*1024*1024), 'image/png')})
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)
