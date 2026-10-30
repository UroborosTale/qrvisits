import re
import uuid
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.core.exceptions import ValidationError


def photo_path(instance, filename):
    return f'photos/{uuid.uuid4().hex}.jpg'


class EmployeeCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField('Ф.И.О. полностью', max_length=180,
        help_text='Фамилия, имя и отчество (при наличии), без сокращений.')
    job_title = models.CharField('Должность', max_length=200, blank=True)
    department = models.CharField('Подразделение', max_length=200, blank=True)
    phone = models.CharField('Рабочий телефон (городской)', max_length=40, blank=True,
        help_text='Например: +7 (495) 000-00-00. Добавочный укажите отдельно.',
        validators=[RegexValidator(r'\A(?=(?:\D*\d){3})\+?[0-9 ()\-]{3,40}\Z', 'Укажите городской номер, например +7 (495) 000-00-00.')])
    phone_extension = models.CharField('Добавочный номер', max_length=10, blank=True,
        help_text='Только цифры, например 0123.', validators=[RegexValidator(r'\A[0-9]{1,10}\Z', 'Добавочный номер должен содержать от 1 до 10 цифр.')])
    mobile_phone = models.CharField('Мобильный телефон', max_length=40, blank=True,
        help_text='Например: +7 (900) 000-00-00.',
        validators=[RegexValidator(r'\A(?=(?:\D*\d){3})\+?[0-9 ()\-]{3,40}\Z', 'Укажите мобильный номер, например +7 (900) 000-00-00.')])
    email = models.EmailField('Рабочая почта', blank=True)
    photo = models.ImageField('Фото', upload_to=photo_path, blank=True)
    description = models.TextField('О сотруднике', max_length=2000, blank=True)
    website = models.URLField('Сайт КМЗ', max_length=500, blank=True, validators=[URLValidator(schemes=['http', 'https'])])
    messenger_url = models.URLField('Мессенджер (https-ссылка)', max_length=500, blank=True,
        validators=[URLValidator(schemes=['http', 'https'])])
    is_active = models.BooleanField('Опубликована', default=False)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Изменена', auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'визитка сотрудника'
        verbose_name_plural = 'визитки сотрудников'

    def __str__(self):
        return self.full_name

    def clean(self):
        super().clean()
        if self.phone_extension and not self.phone:
            raise ValidationError({'phone_extension': 'Сначала укажите рабочий городской телефон.'})

    def get_absolute_url(self):
        return f'/c/{self.pk}/'

    @property
    def initials(self):
        return ''.join(word[0] for word in self.full_name.split()[:2]).upper()

    @property
    def dial_phone(self):
        return re.sub(r'[^+0-9]', '', self.phone)

    @property
    def work_phone_uri(self):
        extension = f';ext={self.phone_extension}' if self.phone_extension else ''
        return f'tel:{self.dial_phone}{extension}'

    @property
    def dial_mobile_phone(self):
        return re.sub(r'[^+0-9]', '', self.mobile_phone)
