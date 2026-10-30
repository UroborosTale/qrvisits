from io import BytesIO
import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from cards.models import EmployeeCard


class PublicTests(TestCase):
    def setUp(self):
        self.card = EmployeeCard.objects.create(full_name='Иван <script>alert(1)</script>',
            job_title='Инженер', email='ivan@example.com', phone='+7 (000) 000-00-00', is_active=True)

    def test_card_is_public_escaped_and_not_cached(self):
        response = self.client.get(self.card.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иван &lt;script&gt;')
        self.assertNotContains(response, '<script>alert')
        self.assertContains(response, 'mailto:ivan@example.com')
        self.assertContains(response, 'tel:+70000000000')
        self.assertIn('noindex', response['X-Robots-Tag'])
        self.assertIn('no-store', response['Cache-Control'])

    def test_unknown_and_disabled_do_not_reveal_identity(self):
        self.card.is_active = False; self.card.save()
        disabled = self.client.get(self.card.get_absolute_url())
        unknown = self.client.get('/c/11111111-1111-1111-1111-111111111111/')
        self.assertEqual(disabled.status_code, 404)
        self.assertEqual(disabled.content, unknown.content)
        self.assertNotContains(disabled, 'ivan@example.com', status_code=404)

    def test_empty_optional_fields_do_not_render_dead_links(self):
        card = EmployeeCard.objects.create(full_name='Пётр Петров', is_active=True)
        response = self.client.get(card.get_absolute_url())
        self.assertContains(response, 'ПП')
        self.assertNotContains(response, 'href="tel:')
        self.assertNotContains(response, 'href="mailto:')
        self.assertNotContains(response, 'Написать')

    def test_draft_preview_is_restricted_to_authorized_staff(self):
        self.card.is_active = False; self.card.save()
        url = f'/manage/preview/{self.card.pk}/'
        self.assertEqual(self.client.get(url).status_code, 302)
        user = get_user_model().objects.create_user('staff', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(url).status_code, 403)
        user.is_superuser = True; user.save()
        self.assertContains(self.client.get(url), 'Черновик')

    def test_photos_serve_only_for_active_cards_and_never_via_media_path(self):
        out = BytesIO(); Image.new('RGB', (10, 10)).save(out, 'JPEG')
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.card.photo = SimpleUploadedFile('face.jpg', out.getvalue(), 'image/jpeg'); self.card.save()
            url = self.card.get_absolute_url() + 'photo/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/jpeg')
            response.close()
            self.assertEqual(self.client.get(self.card.photo.url).status_code, 404)
            self.card.is_active = False; self.card.save()
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_no_public_directory(self):
        response = self.client.get('/')
        self.assertNotContains(response, self.card.full_name)
