import re
from django.core.exceptions import ValidationError


def format_phone(value):
    value = value.replace('\u00a0', ' ').strip()
    if not value:
        return ''
    error = 'Введите полный номер в формате +7 (XXX) XXX-XX-XX. Добавочный укажите отдельно.'
    if not re.fullmatch(r'\+?[0-9 ()-]+', value):
        raise ValidationError(error)
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) == 10 and not value.startswith('+'):
        digits = '7' + digits
    elif len(digits) == 11 and digits.startswith('8') and not value.startswith('+'):
        digits = '7' + digits[1:]
    if len(digits) != 11 or not digits.startswith('7'):
        raise ValidationError(error)
    return f'+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}'


def display_phone(value):
    try:
        return format_phone(value)
    except ValidationError:
        return value  # Keep legacy incomplete data visible for correction.
