from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from users_api.models import ManagerCode

User = get_user_model()


class UserViewSetTests(APITestCase):
    """Тесты для UserViewSet."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="manager123",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="regular123",
            is_manager=False,
        )

    def test_users_list_access_for_manager(self):
        """
        Тест на возможность доступа
        менеджера к списку пользователей.
        """
        self.client.force_authenticate(self.manager)
        url = reverse("users_api:users_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_detail_user_access_for_manager(self):
        """
        Тест на возможность доступа менеджера
        к информации о пользователе.
        """
        self.client.force_authenticate(self.manager)
        url = reverse(
            "users_api:user_detail", kwargs={"pk": self.performer.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.performer.pk)

    def test_users_list_access_for_performer(self):
        """
        Тест на невозможность доступа
        исполнителя к списку пользователей.
        """
        self.client.force_authenticate(self.performer)
        url = reverse("users_api:users_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_user_access_for_performer(self):
        """
        Тест на невозможность доступа
        исполнителя к информации о пользователе.
        """
        self.client.force_authenticate(self.performer)
        url = reverse(
            "users_api:user_detail", kwargs={"pk": self.performer.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegisterAPIViewTests(APITestCase):
    """Тесты для RegisterAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:register")

    def test_register_manager_success(self):
        """Тест на удачную регистрацию менеджера."""
        ManagerCode.objects.create(code="CODE")
        data = {
            "username": "manager",
            "email": "manager@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "KKKKK12345",
            "password2": "KKKKK12345",
            "manager_code": "CODE",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ManagerCode.objects.get(code="CODE").is_used)
        self.assertTrue(User.objects.get(username="manager").is_manager)

    def test_register_performer_success(self):
        """Тест на удачную регистрацию исполнителя."""
        data = {
            "username": "performer",
            "email": "performer@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "KKKKK12345",
            "password2": "KKKKK12345",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(User.objects.get(username="performer").is_manager)

    def test_register_failure_email_exists(self):
        """Тест на ошибку регистрации из-за существующего E-mail."""
        User.objects.create_user(
            username="user",
            email="user@example.com",
            password="manager123",
            is_manager=False,
        )

        data = {
            "username": "performer",
            "email": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "KKKKK12345",
            "password2": "KKKKK12345",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["email"][0], "Такой E-mail уже существует."
        )

    def test_register_failure_passwords_not_equal(self):
        """Тест на ошибку регистрации из-за несовпадения паролей."""
        data = {
            "username": "performer",
            "email": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "KKKKK1234",
            "password2": "KKKKK12345",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password"][0], "Пароли не совпадают.")

    def test_register_failure_used_manager_code(self):
        """
        Тест на ошибку регистрации из-за
        использованного или несуществующего менеджерского кода.
        """
        ManagerCode.objects.create(code="CODE", is_used=True)
        data = {
            "username": "performer",
            "email": "performer@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "KKKKK12345",
            "password2": "KKKKK12345",
            "manager_code": "CODE",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["manager_code"][0],
            "Неверный или использованный код.",
        )


class LoginAPIViewTests(APITestCase):
    """Тесты для LoginAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:token_obtain_pair")

        cls.user_password = "KKKKK12345"
        cls.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password=cls.user_password,
            is_manager=True,
        )

    def test_login_success(self):
        """Тест на успешный логин пользователя."""
        data = {
            "username": self.user.username,
            "password": self.user_password,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)

        self.assertEqual(response.data["id"], self.user.pk)
        self.assertEqual(response.data["is_manager"], self.user.is_manager)

    def test_login_invalid_credentials(self):
        """Тест на неудачную попытку входа с неверными данными."""

        data = {
            "username": self.user.username,
            "password": "wrongpassword",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Пользователь с введёнными данными не найден.",
        )


class ProfileAPIViewTests(APITestCase):
    """Тесты для ProfileAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:profile")

        cls.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="Joe",
            last_name="Joe",
            password="KKKKK12345",
            is_manager=True,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Тест GET-запроса на получение данных из профиля."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)
        self.assertEqual(response.data["patronymic"], self.user.patronymic)
        self.assertTrue(response.data["is_manager"])

    def test_put_profile(self):
        """Тест PUT-запроса для полного обновления профиля."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "patronymic": "Middle",
        }

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(self.user.first_name, data["first_name"])
        self.assertEqual(self.user.last_name, data["last_name"])
        self.assertEqual(self.user.patronymic, data["patronymic"])

    def test_patch_profile(self):
        """Тест PATCH-запроса для частичного обновления профиля."""
        data = {"first_name": "Patched"}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(self.user.first_name, data["first_name"])
        self.assertEqual(self.user.last_name, "Joe")
        self.assertIsNone(self.user.patronymic)

    def test_unauthenticated_access(self):
        """
        Тест отсутствия доступа
        к профилю у неавторизованного пользователя.
        """
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordAPIViewTests(APITestCase):
    """Тесты для ChangePasswordAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:password_change")

        cls.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="Joe",
            last_name="Joe",
            password="KKKKK12345",
            is_manager=True,
        )

        cls.new_password = "new_secure_password"

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        """Тест на успешную смену пароля."""
        data = {
            "old_password": "KKKKK12345",
            "new_password1": self.new_password,
            "new_password2": self.new_password,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Пароль успешно изменён.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_change_password_incorrect_old_password(self):
        """Тест на несовпадение старого пароля."""
        data = {
            "old_password": "wrong_password",
            "new_password1": self.new_password,
            "new_password2": self.new_password,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["old_password"][0], "Старый пароль введён неверно."
        )

    def test_change_password_mismatch_new_passwords(self):
        """Тест на несовпадение новых паролей."""
        data = {
            "old_password": "KKKKK12345",
            "new_password1": self.new_password,
            "new_password2": "different_password",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["new_password2"][0], "Пароли не совпадают."
        )

    def test_change_password_same_as_old(self):
        """Тест на совпадение старого и нового паролей."""
        data = {
            "old_password": "KKKKK12345",
            "new_password1": "KKKKK12345",
            "new_password2": "KKKKK12345",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["new_password2"][0],
            "Новый пароль не может совпадать со старым.",
        )

    def test_unauthenticated_access(self):
        """
        Тест на запрет смены пароля
        для неавторизованного пользователя.
        """
        self.client.force_authenticate(user=None)
        data = {
            "old_password": "old_password",
            "new_password1": self.new_password,
            "new_password2": self.new_password,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetRequestAPIViewTestCase(APITestCase):
    """Тесты для PasswordResetRequestAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:password_reset_request")

        cls.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="Joe",
            last_name="Joe",
            password="KKKKK12345",
            is_manager=True,
        )

    def test_password_reset_request_valid_email(self):
        """Тест запроса на сброс пароля с существующим email."""
        data = {"email": self.user.email}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "Письмо для сброса пароля отправлено на почту."
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_password_reset_request_invalid_email(self):
        """Тест запроса на сброс пароля с несуществующим email."""
        data = {"email": "nonexistent@example.com"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Пользователя с таким E-mail не существует."
        )


class PasswordResetConfirmAPIViewTestCase(APITestCase):
    """Тесты для PasswordResetConfirmAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users_api:password_reset_confirm")

        cls.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Joe",
            last_name="Joe",
            password="secure_password",
            is_manager=True,
        )

        cls.new_password = "new_secure_password"

    def setUp(self):
        self.uidb64 = urlsafe_base64_encode(str(self.user.pk).encode())
        self.token = default_token_generator.make_token(self.user)

    def test_password_reset_confirm_valid_data(self):
        """Тест сброса пароля с корректными данными."""
        data = {
            "new_password1": self.new_password,
            "new_password2": self.new_password,
            "uidb64": self.uidb64,
            "token": self.token,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Пароль был успешно сброшен.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_password_reset_confirm_passwords_do_not_match(self):
        """Тест сброса пароля при несовпадении паролей."""
        data = {
            "new_password1": self.new_password,
            "new_password2": "different_password",
            "uidb64": self.uidb64,
            "token": self.token,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["new_password2"][0], "Пароли не совпадают.")

    def test_password_reset_confirm_invalid_uid(self):
        """Тест сброса пароля с некорректным UID."""
        data = {
            "new_password1": self.new_password,
            "new_password2": self.new_password,
            "uidb64": "invalid_uid",
            "token": self.token,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["uidb64"][0], "Неверная ссылка.")

    def test_password_reset_confirm_invalid_token(self):
        """Тест сброса пароля с некорректным токеном."""
        data = {
            "new_password1": self.new_password,
            "new_password2": self.new_password,
            "uidb64": self.uidb64,
            "token": "invalid_token",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["token"][0], "Неверный или истёкший токен.")
