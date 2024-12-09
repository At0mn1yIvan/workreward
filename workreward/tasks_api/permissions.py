from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    Разрешение для проверки, что пользователь является менеджером.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_manager
        )
