from django.conf import settings
from .qr import canonical_url


def escape(value):
    return str(value).replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    result, current = [], b''
    for character in line:
        chunk = character.encode('utf-8')
        if len(current) + len(chunk) > 75:
            result.append(current)
            current = b' '
        current += chunk
    result.append(current)
    return b'\r\n'.join(result)


def build_vcard(card):
    lines = ['BEGIN:VCARD', 'VERSION:3.0', 'FN:' + escape(card.full_name),
             'N:' + escape(card.full_name) + ';;;;', 'ORG:' + escape(settings.COMPANY_NAME)]
    if card.job_title:
        lines.append('TITLE:' + escape(card.job_title))
    if card.phone:
        lines.append('TEL;TYPE=WORK,VOICE:' + card.dial_phone)
    if card.email:
        lines.append('EMAIL;TYPE=WORK:' + escape(card.email))
    if card.description:
        lines.append('NOTE:' + escape(card.description))
    lines.extend(['URL:' + canonical_url(card), 'END:VCARD'])
    return b'\r\n'.join(fold(line) for line in lines) + b'\r\n'
