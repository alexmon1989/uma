class BiblioDataInvUMLDRawGetMixin:
    def get_biblio_data(self, app_data: dict) -> dict:
        if 'Patent' in app_data:
            return app_data['Patent']
        else:
            return app_data['Claim']
