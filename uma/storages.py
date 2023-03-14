from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class MyStorage(ManifestStaticFilesStorage):
    def __init__(self, *args, **kwargs):
        self.missing_files = []
        super().__init__(*args, **kwargs)

    def hashed_name(self, name, *args, **kwargs):
        """
        Ignore missing files, e.g. non-existent background image referenced from css.
        Returns the original filename if the referenced file doesn't exist.
        """
        try:
            return super().hashed_name(name, *args, **kwargs)
        except ValueError as e:
            message = e.args[0].split(' with ')[0]
            self.missing_files.append(message)
            print(f'\x1b[0;30;41m{message}\x1b[0m')
            return name
