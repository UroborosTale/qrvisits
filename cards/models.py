import re
import uuid
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.urls import reverse


def photo_path(instance, filename):
    return f'photos/{uuid.uuid4().hex}.jpg'


class EmployeeCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField('ФИО', max_length=180)
    job_title = models.CharField('Должность', max_length=200, blank=True)
    phone = models.CharField('Рабочий телефон', max_length=40, blank=True,
        validators=[RegexValidator(r'^\+?[0-9 ()\-]{3,40}$', 'Укажите телефон без добавочного номера и служебных символов.')])
    email = models.EmailField('Рабочая почта', blank=True)
    photo = models.ImageField('Фотография', upload_to=photo_path, blank=True)
    description = models.TextField('О сотруднике', max_length=2000, blank=True)
    website = models.URLField('Сайт', max_length=500, blank=True, validators=[URLValidator(schemes=['http', 'https'])])
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

    def get_absolute_url(self):
        return f'/c/{self.pk}/'

    @property
    def initials(self):
        return ''.join(word[0] for word in self.full_name.split()[:2]).upper()

    @property
    def dial_phone(self):
        return re.sub(r'[^+0-9]', '', self.phone)
