from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from typing import List

UserModel = get_user_model()


class UserService:

    @staticmethod
    def get_user_or_anonymous(user_id) -> UserModel | AnonymousUser:
        """Возвращает пользователя по его id или возвращает анонимного юзера, если он не найден."""
        try:
            user = UserModel.objects.prefetch_related('groups').get(id=user_id)
        except UserModel.DoesNotExist:
            user = AnonymousUser()

        return user

    @staticmethod
    def get_user_groups(user_id) -> List[str]:
        """Возвращает список групп пользователя."""
        user = UserModel.objects.filter(id=user_id).prefetch_related('groups').first()
        res = []
        for group in user.groups.all():
            res.append(group.name)
        return res
