from common.pagination import APIListPagination
from common.permissions import IsManager
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .utils import send_password_reset_link
from . import serializers
from .renderers import UserJSONRenderer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для получения объектов пользователей.

    Этот ViewSet предоставляет стандартные действия для получения
    пользователей. Для доступа к списку пользователей
    требуется роль менеджера.

    Атрибуты:
        - queryset (QuerySet): Все пользователи,
        получаемые из модели пользователя.
        - permission_classes (tuple): Кортеж с классами разрешений,
        в данном случае доступ к действиям имеют только менеджеры.
        - renderer_classes (tuple): Кортеж с классами рендереров.
        Для сериализации используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для преобразования данных
        о пользователях в формат JSON.
        - pagination_class (class): Класс пагинации, применяемый
        для результатов запроса.
    """

    queryset = User.objects.all()
    permission_classes = (IsManager,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.UserSerializer
    pagination_class = APIListPagination


class RegisterAPIView(APIView):
    """
    Представление для регистрации нового пользователя.

    Это представление предоставляет возможность создать нового
    пользователя через POST-запрос.
    При успешной регистрации возвращается статус 201 и данные о пользователе.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        в данном случае доступ разрешен любому пользователю.
        - renderer_classes (tuple): Кортеж с классами рендереров.
        Для сериализации используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для регистрации
        нового пользователя.

    Методы:
        - post(request, *args, **kwargs): Обрабатывает POST-запрос
        для регистрации нового пользователя. Валидирует данные,
        создает пользователя и возвращает информацию о новом пользователе.
    """

    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.RegisterUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    Представление для логина пользователя.

    Это представление позволяет пользователю выполнить вход в систему,
    предоставив свои учетные данные (имя пользователя и пароль).
    При успешной аутентификации генерируется и возвращается пара JWT токенов
    (refresh и access), а также информация о пользователе.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        в данном случае доступ разрешен любому пользователю.
        - renderer_classes (tuple): Кортеж с классами рендереров.
        Для сериализации используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для
        аутентификации пользователя.

    Методы:
        - post(request, *args, **kwargs): Обрабатывает POST-запрос
        для логина пользователя. Валидирует данные,
        аутентифицирует пользователя и генерирует токены.
    """

    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user_obj"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "is_manager": user.is_manager,
                "id": user.pk,
            },
            status=status.HTTP_200_OK,
        )


class ProfileAPIView(APIView):
    """
    Представление для получения и изменения профиля пользователя.

    Это представление позволяет пользователю получить,
    обновить или частично обновить свои данные.
    Доступно только для аутентифицированных пользователей.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        только для аутентифицированных пользователей.
        - renderer_classes (tuple): Кортеж с классами рендереров, в данном
        случае используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для работы с
        профилем пользователя.

    Методы:
        - get(request, *args, **kwargs): Получение данных профиля пользователя.
        - put(request, *args, **kwargs): Полное обновление
        данных профиля пользователя.
        - patch(request, *args, **kwargs): Частичное обновление
        данных профиля пользователя.
    """
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.ProfileUserSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Представление для изменения пароля пользователя.

    Это представление позволяет пользователю изменить свой пароль,
    предоставив старый и новый пароли.
    Доступно только для аутентифицированных пользователей.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        только для аутентифицированных пользователей.
        - renderer_classes (tuple): Кортеж с классами рендереров,
        в данном случае используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для изменения
        пароля пользователя.

    Методы:
        - post(request, *args, **kwargs): Обработка запроса для
        изменения пароля пользователя.
    """
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.UserPasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestAPIView(APIView):
    """
    Представление для запроса сброса пароля пользователя.

    Это представление позволяет пользователю запросить сброс пароля,
    отправив запрос на указанный email.
    Доступно для всех пользователей.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        доступно для всех пользователей.
        - renderer_classes (tuple): Кортеж с классами рендереров,
        в данном случае используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для запроса
        сброса пароля пользователя.

    Методы:
        - post(request, *args, **kwargs): Обработка запроса для отправки письма
        с ссылкой на сброс пароля.
    """

    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.UserPasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user_obj"]
        email = serializer.validated_data["email"]
        
        send_password_reset_link(user, email, request)
        # try:
        #     send_password_reset_link(user, email, request)
        # except Exception as e:
        #     return Response(
        #         {"detail": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

        return Response(
            {"message": "Письмо для сброса пароля отправлено на почту."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmAPIView(APIView):
    """
    Представление для подтверждения сброса пароля пользователя.

    Это представление позволяет пользователю подтвердить сброс пароля с
    использованием предоставленных данных и установить новый пароль.
    Доступно для всех пользователей, предоставляющих правильные данные.

    Атрибуты:
        - permission_classes (tuple): Кортеж с классами разрешений,
        доступно для всех пользователей.
        - renderer_classes (tuple): Кортеж с классами рендереров,
        в данном случае используется `UserJSONRenderer`.
        - serializer_class (class): Сериализатор для подтверждения
        сброса пароля и установки нового пароля.

    Методы:
        - post(request, *args, **kwargs): Обработка запроса для сброса
        пароля и установки нового пароля.
    """

    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = serializers.UserPasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Пароль был успешно сброшен."},
            status=status.HTTP_200_OK,
        )
