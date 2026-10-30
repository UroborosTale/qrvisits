from io import BytesIO, StringIO
import uuid
from PIL import Image
import zxingcpp
from django.core.management import call_command
from django.test import TestCase, override_settings
from cards.models import EmployeeCard
from cards.services.vcard import build_vcard
from cards.services.qr import canonical_url, make_qr


@override_settings(PUBLIC_BASE_URL='https://cards.example.com')
class ExportTests(TestCase):
    def setUp(self):
        self.card = EmployeeCard.objects.create(id=uuid.UUID('11111111-1111-1111-1111-111111111111'),
            full_name='Иван Иванов', email='ivan@example.com', phone='+7 (000) 000-00-00', is_active=True)

    def test_vcard_cyrillic_escaping_and_line_folding(self):
        self.card.full_name = 'Иван, Иванов;\\\nTEL:911'
        self.card.description = 'Я' * 150
        self.card.job_title = 'Главный инженер'
        payload = build_vcard(self.card)
        self.assertTrue(payload.endswith(b'END:VCARD\r\n'))
        self.assertTrue(payload.startswith(b'BEGIN:VCARD\r\nVERSION:3.0\r\n'))
        self.assertNotIn(b'\r\nTEL:911', payload)
        for line in payload.split(b'\r\n'):
            self.assertLessEqual(len(line), 75)
            line.decode('utf-8')
        unfolded = payload.replace(b'\r\n ', b'').decode('utf-8')
        self.assertIn('FN:Иван\\, Иванов\\;\\\\\\nTEL:911\r\n', unfolded)
        self.assertIn('TITLE:Главный инженер\r\n', unfolded)
        self.assertIn('TEL;TYPE=WORK,VOICE:+70000000000\r\n', unfolded)
        self.assertIn('EMAIL;TYPE=WORK:ivan@example.com\r\n', unfolded)

    @override_settings(ALLOWED_HOSTS=['testserver', 'evil.example'])
    def test_qr_png_decodes_to_canonical_url_independent_of_host(self):
        url = '/c/11111111-1111-1111-1111-111111111111/'
        expected = 'https://cards.example.com' + url
        response = self.client.get(url + 'qr.png', HTTP_HOST='evil.example')
        self.assertEqual(response.status_code, 200)
        decoded = zxingcpp.read_barcode(Image.open(BytesIO(response.content)))
        self.assertEqual(decoded.text, expected)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(canonical_url(self.card), expected)
        self.card.full_name = 'Другое имя'; self.card.save()
        self.assertEqual(canonical_url(self.card), expected)
        self.assertEqual(self.client.get(url+'qr.png').content, response.content)

    def test_svg_qr_uses_same_payload(self):
        response = self.client.get(self.card.get_absolute_url() + 'qr.svg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn(b'<svg', response.content)
        # Rasterize the SVG independently and decode it, rather than inspecting source paths.
        from xml.etree import ElementTree as ET
        from PIL import ImageDraw
        svg = ET.fromstring(response.content)
        scale = 20
        number = lambda v: float(v.removesuffix('mm'))
        raster = Image.new('RGB', (round(number(svg.attrib['width'])*scale), round(number(svg.attrib['height'])*scale)), 'white')
        draw = ImageDraw.Draw(raster)
        for rect in svg.findall('{http://www.w3.org/2000/svg}rect'):
            x, y, w, h = [round(number(rect.attrib[key])*scale) for key in ('x', 'y', 'width', 'height')]
            draw.rectangle((x, y, x+w-1, y+h-1), fill='black')
        self.assertEqual(zxingcpp.read_barcode(raster).text,
            'https://cards.example.com/c/11111111-1111-1111-1111-111111111111/')

    def test_export_endpoints_and_disabled_identity(self):
        url = self.card.get_absolute_url()
        response = self.client.get(url+'contact.vcf')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('text/vcard', response['Content-Type'])
        self.card.is_active=False; self.card.save()
        for suffix in ['contact.vcf', 'qr.png', 'qr.svg']:
            result = self.client.get(url+suffix)
            self.assertEqual(result.status_code, 404)
            self.assertNotIn(b'ivan@example.com', result.content)

    def test_invalid_qr_format_rejected(self):
        with self.assertRaises(ValueError):
            make_qr(self.card, 'html')

    def test_inline_qr_is_viewable(self):
        response = self.client.get(self.card.get_absolute_url()+'qr.png?inline=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('inline', response['Content-Disposition'])


class SeedTests(TestCase):
    def test_demo_seed_is_idempotent_and_does_not_change_existing_cards(self):
        stream = StringIO()
        call_command('seed_demo', stdout=stream)
        self.assertEqual(EmployeeCard.objects.count(), 5)
        first = EmployeeCard.objects.first()
        first.full_name = 'Изменено администратором'; first.save()
        call_command('seed_demo', stdout=stream)
        self.assertEqual(EmployeeCard.objects.count(), 5)
        first.refresh_from_db()
        self.assertEqual(first.full_name, 'Изменено администратором')
        self.assertTrue(all(c.email.endswith('@example.com') for c in EmployeeCard.objects.all()))
