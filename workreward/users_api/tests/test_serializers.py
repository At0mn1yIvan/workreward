from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIRequestFactory

from users_api import serializers
from users_api.models import ManagerCode


class UserSerializerTestCase(TestCase):
    """Тесты для сериализатора UserSerializer."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="testpassword123",
        )
        self.expected_data = {
            "id": self.user.id,
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "patronymic": "Smith",
            "is_manager": False,  # Поле по умолчанию
        }

    def test_serialization(self):
        """Тест сериализации данных пользователя."""
        serializer = serializers.UserSerializer(instance=self.user)
        self.assertEqual(serializer.data, self.expected_data)


class LoginUserSerializerTestCase(TestCase):
    """Тесты для сериализатора LoginUserSerializer."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="testpassword123",
        )

    def test_successful_authentication(self):
        """Тест успешной аутентификации пользователя."""
        valid_data = {
            "username": "testuser",
            "password": "testpassword123",
        }
        serializer = serializers.LoginUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["user_obj"], self.user)

    def test_successful_authentication_email(self):
        """Тест успешной аутентификации пользователя по E-mail."""
        valid_data = {
            "username": "testuser@example.com",
            "password": "testpassword123",
        }
        serializer = serializers.LoginUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["user_obj"], self.user)

    def test_failed_authentication_invalid_password(self):
        """Тест неуспешной аутентификации из-за некорректного пароля."""
        invalid_data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        serializer = serializers.LoginUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["detail"][0],
            "Пользователь с введёнными данными не найден.",
        )

    def test_failed_authentication_invalid_username(self):
        """Тест неуспешной аутентификации из-за некорректного имени пользователя."""
        invalid_data = {
            "username": "nonexistentuser",
            "password": "testpassword123",
        }
        serializer = serializers.LoginUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["detail"][0],
            "Пользователь с введёнными данными не найден.",
        )

    def test_missing_fields(self):
        """Тест валидации при отсутствии обязательных полей."""
        invalid_data = {}
        serializer = serializers.LoginUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("password", serializer.errors)


class RegisterUserSerializerTestCase(TestCase):
    """Тесты для сериализатора RegisterUserSerializer."""

    def setUp(self):
        self.existing_user = get_user_model().objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="KKKKK_12345",
        )
        self.valid_manager_code = ManagerCode.objects.create(
            code="VALIDCODE",
        )

    def test_successful_registration(self):
        """Тест успешной регистрации нового пользователя."""
        valid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "KKKKK_12345",
            "password2": "KKKKK_12345",
            "manager_code": "VALIDCODE",
        }
        serializer = serializers.RegisterUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.is_manager)
        self.assertTrue(ManagerCode.objects.get(code="VALIDCODE").is_used)

    def test_duplicate_email(self):
        """Тест ошибки при дублировании email."""
        invalid_data = {
            "username": "anotheruser",
            "email": "existinguser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "KKKKK_12345",
            "password2": "KKKKK_12345",
        }
        serializer = serializers.RegisterUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"][0], "Такой E-mail уже существует."
        )

    def test_password_mismatch(self):
        """Тест ошибки при несовпадении паролей."""
        invalid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "KKKKK_12345",
            "password2": "KKKKK_1234",
        }
        serializer = serializers.RegisterUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors["password"][0], "Пароли не совпадают."
        )

    def test_invalid_manager_code(self):
        """Тест ошибки при использовании неверного или использованного кода менеджера."""
        invalid_code_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "KKKKK_12345",
            "password2": "KKKKK_12345",
            "manager_code": "INVALIDCODE",
        }
        serializer = serializers.RegisterUserSerializer(data=invalid_code_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("manager_code", serializer.errors)
        self.assertEqual(
            serializer.errors["manager_code"][0],
            "Неверный или использованный код.",
        )

    def test_weak_password(self):
        """Тест ошибки при вводе слабого пароля."""
        invalid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "123",
            "password2": "123",
        }
        serializer = serializers.RegisterUserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_registration_without_manager_code(self):
        """Тест успешной регистрации без указания кода менеджера."""
        valid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "KKKKK_12345",
            "password2": "KKKKK_12345",
        }
        serializer = serializers.RegisterUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertFalse(user.is_manager)

    def test_registration_with_optional_patronymic(self):
        """Тест успешной регистрации с указанием отчества."""
        valid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "patronymic": "MiddleName",
            "password": "KKKKK_12345",
            "password2": "KKKKK_12345",
        }
        serializer = serializers.RegisterUserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.patronymic, "MiddleName")


class ProfileUserSerializerTest(TestCase):
    """Тесты для сериализатора ProfileUserSerializer."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            patronymic="Patronymic",
            password="password123",
            is_manager=False,
        )
        self.serializer = serializers.ProfileUserSerializer(instance=self.user)

    def test_read_only_fields(self):
        """Тест для проверки на неизменяемость полей username, email и is_manager."""
        data = {
            "username": "new_username",
            "email": "new_email@example.com",
            "first_name": "UpdatedFirstName",
            "last_name": "UpdatedLastName",
            "is_manager": True,
        }
        serializer = serializers.ProfileUserSerializer(
            instance=self.user, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, self.user.username)
        self.assertEqual(updated_user.email, self.user.email)
        self.assertEqual(updated_user.is_manager, self.user.is_manager)

    def test_update_user(self):
        """Тест для проверки на обновляемость полей first_name, last_name и patronymic."""
        data = {
            "first_name": "UpdatedFirstName",
            "last_name": "UpdatedLastName",
            "patronymic": "UpdatedPatronymic",
        }
        serializer = serializers.ProfileUserSerializer(
            instance=self.user, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, "UpdatedFirstName")
        self.assertEqual(updated_user.last_name, "UpdatedLastName")
        self.assertEqual(updated_user.patronymic, "UpdatedPatronymic")

    def test_missing_required_fields(self):
        """Тест на отсутствие обязательных полей."""
        data = {
            "first_name": "",
            "last_name": "",
        }
        serializer = serializers.ProfileUserSerializer(
            instance=self.user, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("first_name", serializer.errors)
        self.assertIn("last_name", serializer.errors)

    def test_optional_patronymic_field(self):
        """Тест на проверку необязательности ввода поля patronymic."""
        data = {
            "first_name": "UpdatedFirstName",
            "last_name": "UpdatedLastName",
            "patronymic": None,
        }
        serializer = serializers.ProfileUserSerializer(
            instance=self.user, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, "UpdatedFirstName")
        self.assertEqual(updated_user.last_name, "UpdatedLastName")
        self.assertIsNone(updated_user.patronymic)


class UserPasswordChangeSerializerTests(TestCase):
    def setUp(self):
        """Создаем пользователя для тестов."""
        self.user = get_user_model().objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="old_password",
        )
        self.request = self._get_request_for_user(self.user)

    def _get_request_for_user(self, user):
        """Возвращает объект запроса для пользователя."""
        request = APIRequestFactory().post("test_url/", data={})
        request.user = user
        return request

    def test_serializer_valid_data(self):
        """Тест успешной валидации и сохранения."""
        data = {
            "old_password": "old_password",
            "new_password1": "new_secure_password",
            "new_password2": "new_secure_password",
        }
        serializer = serializers.UserPasswordChangeSerializer(
            data=data,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(self.user.check_password("new_secure_password"))

    def test_serializer_invalid_old_password(self):
        """Тест ошибки при неверном старом пароле."""
        data = {
            "old_password": "wrong_password",
            "new_password1": "new_secure_password",
            "new_password2": "new_secure_password",
        }
        serializer = serializers.UserPasswordChangeSerializer(
            data=data,
            context={"request": self.request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)
        self.assertEqual(
            serializer.errors["old_password"][0],
            "Старый пароль введён неверно.",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old_password"))

    def test_serializer_passwords_do_not_match(self):
        """Тест ошибки при несовпадении паролей."""
        data = {
            "old_password": "old_password",
            "new_password1": "new_secure_password",
            "new_password2": "different_password",
        }
        serializer = serializers.UserPasswordChangeSerializer(
            data=data,
            context={"request": self.request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password2", serializer.errors)
        self.assertEqual(
            serializer.errors["new_password2"][0],
            "Пароли не совпадают.",
        )

    def test_serializer_new_password_same_as_old(self):
        """Тест ошибки, если новый пароль совпадает со старым."""
        data = {
            "old_password": "old_password",
            "new_password1": "old_password",
            "new_password2": "old_password",
        }
        serializer = serializers.UserPasswordChangeSerializer(
            data=data,
            context={"request": self.request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password2", serializer.errors)
        self.assertEqual(
            serializer.errors["new_password2"][0],
            "Новый пароль не может совпадать со старым.",
        )


class UserPasswordResetRequestSerializerTests(TestCase):
    def setUp(self):
        """Создаем пользователей для тестов."""
        self.existing_user = get_user_model().objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="old_password",
        )

    def test_serializer_valid_email(self):
        """Тест успешной валидации с существующим пользователем."""
        data = {"email": "existinguser@example.com"}
        serializer = serializers.UserPasswordResetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["user_obj"], self.existing_user
        )

    def test_serializer_invalid_email(self):
        """Тест ошибки при несуществующем пользователе."""
        data = {"email": "nonexistentuser@example.com"}
        serializer = serializers.UserPasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertEqual(
            serializer.errors["detail"][0],
            "Пользователя с таким E-mail не существует.",
        )

    def test_serializer_invalid_email_format(self):
        """Тест ошибки при неправильном формате email."""
        data = {"email": "invalidemail.com"}
        serializer = serializers.UserPasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class UserPasswordResetConfirmSerializerTests(TestCase):
    def setUp(self):
        """Создаем пользователя для тестов и генерируем токен."""
        self.user = get_user_model().objects.create_user(
            username="existinguser",
            email="existinguser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="old_password",
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_serializer_valid_data(self):
        """Тест успешного сброса пароля с валидными данными."""
        data = {
            "new_password1": "new_secure_password",
            "new_password2": "new_secure_password",
            "uidb64": self.uidb64,
            "token": self.token,
        }
        serializer = serializers.UserPasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(user.check_password("new_secure_password"))

    def test_serializer_passwords_do_not_match(self):
        """Тест ошибки при несовпадении паролей."""
        data = {
            "new_password1": "new_secure_password",
            "new_password2": "different_password",
            "uidb64": self.uidb64,
            "token": self.token,
        }
        serializer = serializers.UserPasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password2", serializer.errors)
        self.assertEqual(
            serializer.errors["new_password2"][0], "Пароли не совпадают."
        )

    def test_serializer_invalid_uidb64(self):
        """Тест ошибки при неверной ссылке (uidb64)."""
        data = {
            "new_password1": "new_secure_password",
            "new_password2": "new_secure_password",
            "uidb64": "invalid_uidb64",
            "token": self.token,
        }
        serializer = serializers.UserPasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uidb64", serializer.errors)
        self.assertEqual(
            serializer.errors["uidb64"][0], "Неверная ссылка."
        )

    def test_serializer_invalid_token(self):
        """Тест ошибки при неверном или истекшем токене."""
        data = {
            "new_password1": "new_secure_password",
            "new_password2": "new_secure_password",
            "uidb64": self.uidb64,
            "token": "wrong_token",
        }
        serializer = serializers.UserPasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        self.assertEqual(
            serializer.errors["token"][0], "Неверный или истёкший токен."
        )

    def test_serializer_invalid_password_format(self):
        """Тест ошибки при некорректном формате пароля."""
        data = {
            "new_password1": "short",
            "new_password2": "short",
            "uidb64": self.uidb64,
            "token": self.token,
        }
        serializer = serializers.UserPasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password1", serializer.errors)
