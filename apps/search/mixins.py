class BiblioDataInvUMLDRawGetMixin:
    def get_biblio_data(self, app_data: dict) -> dict:
        if 'Patent' in app_data:
            return app_data['Patent']
        elif 'Claim' in app_data:
            return app_data['Claim']
        return {}


class BiblioDataCRRawGetMixin:
    def get_biblio_data(self, app_data: dict) -> dict:
        if 'Certificate' in app_data:
            return app_data['Certificate']['CopyrightDetails']
        elif 'DecisionDetails' in app_data:
            return app_data['Decision']['DecisionDetails']
        return {}
