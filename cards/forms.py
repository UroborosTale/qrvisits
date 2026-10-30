import warnings
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django import forms
from django.core.files.base import ContentFile
from .models import EmployeeCard


class EmployeeCardForm(forms.ModelForm):
    class Meta:
        model = EmployeeCard
        fields = ['photo', 'full_name', 'job_title', 'department', 'phone', 'phone_extension',
                  'mobile_phone', 'email', 'description', 'messenger_url', 'is_active']

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
