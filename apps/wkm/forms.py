from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io

from .models import WKMMark


class WKMMarkAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False, label='Зображення')
    ready_for_search_indexation = forms.BooleanField(
        required=False,
        label='Запис готовий для додання у пошуковий індекс СІС',
        help_text='При активуванні цієї опції дані цього запису будуть невдовзі оновлені у пошуковому індексі СІС.'
    )

    class Meta:
        model = WKMMark
        fields = '__all__'
        exclude = ('mark_image',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.mark_image:
            # Создаем файл изображения из бинарных данных
            image = Image.open(io.BytesIO(self.instance.mark_image))
            output = io.BytesIO()
            image.save(output, format='JPEG')
            output.seek(0)
            self.fields['image'].initial = InMemoryUploadedFile(
                output, 'ImageField', f"{self.instance.pk}.jpg", 'image/jpeg', output.getbuffer().nbytes, None
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('image'):
            # Сохраняем изображение в BinaryField
            image = self.cleaned_data['image']
            image_data = image.read()
            instance.mark_image = image_data

        if commit:
            instance.save()
        return instance
