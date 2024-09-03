from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io

from .models import WKMMark
from .tasks import import_wkm


class WKMMarkAdminForm(forms.ModelForm):
    """Клас форми для створення/редагування добре відомої ТМ."""
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
            # Створюємо файл зображення з бінарних даних
            image = Image.open(io.BytesIO(self.instance.mark_image))
            output = io.BytesIO()
            image.save(output, format='JPEG')
            output.seek(0)
            self.fields['image'].initial = InMemoryUploadedFile(
                output, 'ImageField', f"{self.instance.pk}.jpg", 'image/jpeg', output.getbuffer().nbytes, None
            )

    def save(self, commit=True) -> WKMMark:
        instance = super().save(commit=False)
        if self.cleaned_data.get('image'):
            image = self.cleaned_data['image']
            image_data = image.read()
            instance.mark_image = image_data

        if commit:
            instance.save()

        if self.cleaned_data.get('ready_for_search_indexation'):
            # Імпорт добре відомої ТМ у СІС
            import_wkm.delay(instance.id)

        return instance
