from django.contrib.auth.models import User

class EUSignBackend:

    def authenticate(self, request, certificate=None):

        if certificate.is_confirmed:
            return certificate.user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
