from io import BytesIO
import qrcode
import qrcode.image.svg
from django.conf import settings


def canonical_url(card):
    return settings.PUBLIC_BASE_URL + card.get_absolute_url()


def make_qr(card, format):
    if format not in {'png', 'svg'}:
        raise ValueError('Unsupported QR format')
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=4)
    qr.add_data(canonical_url(card))
    qr.make(fit=True)
    image = qr.make_image(image_factory=qrcode.image.svg.SvgImage) if format == 'svg' else qr.make_image()
    output = BytesIO()
    image.save(output)
    return output.getvalue()
