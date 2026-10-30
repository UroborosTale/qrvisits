import os
import subprocess
import sys
from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def configured(self, **changes):
        env = {**os.environ, 'KMZ_ENV': 'production',
            'SECRET_KEY': 'test-only-' + 'AbCdEFgH1234567890'*4,
            'ALLOWED_HOSTS': 'cards.example.com', 'PUBLIC_BASE_URL': 'https://cards.example.com',
            'POSTGRES_HOST': 'db', 'POSTGRES_PASSWORD': 'not-a-real-password'}
        env.update(changes)
        return subprocess.run([sys.executable, '-c',
            'from config import settings; print(settings.DEBUG, settings.SESSION_COOKIE_SECURE)'],
            env=env, capture_output=True, text=True)

    def test_production_requires_explicit_secure_configuration(self):
        for changes in [{'SECRET_KEY': ''}, {'SECRET_KEY': 'CHANGE_ME_'+'x'*60},
                        {'SECRET_KEY': 'short'}, {'PUBLIC_BASE_URL': 'http://cards.example.com'},
                        {'PUBLIC_BASE_URL': 'https://cards.example.com/path'},
                        {'ALLOWED_HOSTS': '*'}, {'POSTGRES_HOST': ''},
                        {'POSTGRES_PASSWORD': 'CHANGE_ME_GENERATE_A_PASSWORD'}]:
            with self.subTest(changes=list(changes)):
                self.assertNotEqual(self.configured(**changes).returncode, 0)

    def test_production_uses_secure_cookies_and_disables_debug(self):
        result = self.configured()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'False True')
