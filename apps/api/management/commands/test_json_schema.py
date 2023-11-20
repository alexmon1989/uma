from django.core.management.base import BaseCommand
from django.conf import settings
from ...models import OpenData
from ...serializers import OpenDataSerializerV1

from jsonschema import validate, Draft202012Validator, ValidationError

import json
import os


class Command(BaseCommand):
    schema: dict = None

    def handle(self, *args, **options):
        with open(os.path.join(settings.BASE_DIR, 'apps', 'api', 'json_schema', 'trademark.json')) as f:
            self.schema = json.load(f)

        apps = OpenData.objects.filter(
            obj_type_id__in=(4,)
        ).select_related(
            'obj_type'
        ).order_by(
            'pk'
        ).values(
            'id',
            'obj_type_id',
            'obj_state',
            'app_number',
            'app_date',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
            'data_docs',
            'data_payments',
            'obj_type__obj_type_ua',
            'files_path',
        )
        c = apps.count()
        i = 0
        for app in apps.iterator(chunk_size=50):
            i += 1
            serializer = OpenDataSerializerV1(app)
            print(f"{i}/{c} - {app['app_number']}")
            try:
                validate(instance=serializer.data, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
            except ValidationError as error:
                if "None is not of type" in str(error):
                    continue
                else:
                    print(error)
                    return
