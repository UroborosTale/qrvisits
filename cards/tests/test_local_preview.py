from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings


@override_settings(DEVELOPMENT=True, DEBUG=True, ALLOWED_HOSTS=['127.0.0.1', 'testserver'])
class LocalPreviewLoginTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser('preview', 'preview@example.com', 'Local-test-password-123')

    def submit(self, *, token=True, host='127.0.0.1', remote='127.0.0.1', site='same-origin'):
        client = Client(enforce_csrf_checks=True)
        client.get('/manage/login/', HTTP_HOST=host)
        data = {'username': 'preview', 'password': 'Local-test-password-123'}
        if token:
            data['csrfmiddlewaretoken'] = client.cookies['csrftoken'].value
        response = client.post('/manage/login/', data, HTTP_HOST=host,
            REMOTE_ADDR=remote, HTTP_ORIGIN='null', HTTP_SEC_FETCH_SITE=site)
        return client, response

    def test_embedded_same_origin_loopback_login_retains_csrf_validation(self):
        client, response = self.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get('/manage/', HTTP_HOST='127.0.0.1').status_code, 200)

    def test_missing_token_stays_forbidden(self):
        self.assertEqual(self.submit(token=False)[1].status_code, 403)

    def test_cross_site_or_missing_metadata_stays_forbidden(self):
        for site in ['cross-site', 'same-site', 'none', '']:
            with self.subTest(site=site):
                self.assertEqual(self.submit(site=site)[1].status_code, 403)

    def test_nonlocal_host_or_remote_stays_forbidden(self):
        self.assertEqual(self.submit(host='testserver')[1].status_code, 403)
        self.assertEqual(self.submit(remote='192.168.1.10')[1].status_code, 403)

    @override_settings(DEVELOPMENT=False, DEBUG=False)
    def test_production_stays_forbidden(self):
        self.assertEqual(self.submit()[1].status_code, 403)
