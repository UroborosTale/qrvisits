import warnings
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django import forms
from django.core.files.base import ContentFile
from .models import EmployeeCard
from .phones import format_phone, display_phone


class EmployeeCardForm(forms.ModelForm):
    class Media:
        js = ['cards/phone-format.js']

    class Meta:
        model = EmployeeCard
        fields = ['photo', 'full_name', 'job_title', 'department', 'phone', 'phone_extension',
                  'mobile_phone', 'email', 'description', 'messenger_url', 'is_active']
        widgets = {
            name: forms.TextInput(attrs={'type': 'tel', 'inputmode': 'tel',
                'placeholder': '+7 (XXX) XXX-XX-XX', 'data-phone-format': 'ru'})
            for name in ('phone', 'mobile_phone')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('phone', 'mobile_phone'):
            self.initial[name] = display_phone(self.initial.get(name, ''))

    def clean_phone(self):
        return format_phone(self.cleaned_data.get('phone', ''))

    def clean_mobile_phone(self):
        return format_phone(self.cleaned_data.get('mobile_phone', ''))

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo or 'photo' not in self.files:
            return photo
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Размер фотографии должен быть не больше 5 МБ.')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                photo.seek(0)
                with Image.open(photo) as source:
                    if source.width * source.height > 20_000_000:
                        raise forms.ValidationError('Фотография должна быть не больше 20 мегапикселей.')
                    if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                        raise forms.ValidationError('Используйте JPG, PNG или WebP.')
                    source.load()
                    image = ImageOps.exif_transpose(source).convert('RGB')
                    image.thumbnail((1600, 1600))
                    # A fresh image deliberately drops EXIF, ICC and other metadata.
                    clean = Image.new('RGB', image.size)
                    clean.paste(image)
                    output = BytesIO()
                    clean.save(output, 'JPEG', quality=88, optimize=True)
            return ContentFile(output.getvalue(), name='photo.jpg')
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            raise forms.ValidationError('Не удалось прочитать фотографию.') from exc
