import datetime
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tasks_api.models import Task
from reports_api.models import TaskReport

User = get_user_model()


class TaskReportViewSetTests(APITestCase):
    """Тесты для TaskReportViewSet."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="password",
            is_manager=False,
        )
        cls.task = Task.objects.create(
            title="Task",
            difficulty=3,
            task_duration=datetime.timedelta(hours=2),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )
        cls.task_report = TaskReport.objects.create(
            text="Test report text",
            efficiency_score=4.5,
            is_awarded=True,
            task=cls.task,
        )

    def test_list_reports_for_manager(self):
        """
        Тест на получение списка отчётов для менеджера.
        Менеджер должен видеть только отчёты своих задач.
        """
        self.client.force_authenticate(user=self.manager)
        url = reverse("reports_api:report_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_reports_for_performer(self):
        """
        Тест на получение списка отчётов для исполнителя.
        Исполнитель должен видеть только
        отчёты задач, в которых он исполнитель.
        """
        self.client.force_authenticate(user=self.performer)
        url = reverse("reports_api:report_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_report_for_manager(self):
        """
        Тест на доступ к конкретному отчёту для менеджера.
        Менеджер может видеть отчёты своих задач.
        """
        self.client.force_authenticate(user=self.manager)
        url = reverse(
            "reports_api:report_detail", kwargs={"pk": self.task_report.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task_report.pk)

    def test_retrieve_report_for_performer(self):
        """
        Тест на доступ к конкретному отчёту для исполнителя.
        Исполнитель может видеть отчёты своих задач.
        """
        self.client.force_authenticate(user=self.performer)
        url = reverse(
            "reports_api:report_detail", kwargs={"pk": self.task_report.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task_report.pk)

    def test_list_reports_for_unauthenticated_user(self):
        """
        Тест на невозможность получения списка отчётов
        неаутентифицированным пользователем.
        """
        url = reverse("reports_api:report_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_report_for_unauthenticated_user(self):
        """
        Тест на невозможность получения отчёта
        неаутентифицированным пользователем.
        """
        url = reverse(
            "reports_api:report_detail", kwargs={"pk": self.task_report.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_cannot_access_other_users_reports(self):
        """
        Тест на невозможность доступа менеджера
        к отчётам задач других пользователей.
        """
        other_manager = User.objects.create_user(
            username="other_manager",
            email="other_manager@example.com",
            password="password",
            is_manager=True,
        )
        self.client.force_authenticate(user=other_manager)
        url = reverse(
            "reports_api:report_detail", kwargs={"pk": self.task_report.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskReportCreateAPIViewTests(APITestCase):
    """Тесты для TaskReportCreateAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="password",
            is_manager=False,
        )
        cls.task = Task.objects.create(
            title="Task",
            difficulty=3,
            task_duration=datetime.timedelta(hours=2),
            time_start=timezone.now(),
            time_completion=timezone.now(),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )

        cls.url = reverse(
            "reports_api:report_create", kwargs={"task_pk": cls.task.pk}
        )

    def test_create_report_as_performer(self):
        """Тест на создание отчёта исполнителем задачи."""
        self.client.force_authenticate(user=self.performer)
        data = {"text": "Task report text"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Task report text")
        self.assertIn("efficiency_score", response.data)

    def test_create_report_as_manager(self):
        """Тест на запрет создания отчёта менеджером."""
        self.client.force_authenticate(user=self.manager)
        data = {"text": "Task report text"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_report_as_performer_not_assigned(self):
        """Тест на запрет создания отчёта для не назначенного исполнителя."""
        other_task = Task.objects.create(
            title="Other Task",
            difficulty=3,
            task_duration=datetime.timedelta(hours=2),
            task_creator=self.manager,
            task_performer=self.manager,
        )
        self.client.force_authenticate(user=self.performer)
        url = reverse(
            "reports_api:report_create", kwargs={"task_pk": other_task.pk}
        )
        data = {"text": "Task report text"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Вы не являетесь исполнителем данной задачи.",
        )

    def test_create_report_for_incomplete_task(self):
        """Тест на запрет создания отчёта для незавершённой задачи."""
        self.client.force_authenticate(user=self.performer)
        self.task.time_completion = None
        self.task.save()
        data = {"text": "Task report text"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0], "Задача ещё не завершена."
        )

    def test_create_report_if_exists(self):
        """Тест на запрет создания отчёта, если отчёт уже существует."""

        TaskReport.objects.create(
            text="Existing report",
            efficiency_score=5,
            task=self.task,
            time_create=timezone.now(),
        )
        self.client.force_authenticate(user=self.performer)
        url = self.url.format(task_pk=self.task.pk)
        data = {"text": "New report text"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0], "Отчёт для этой задачи уже создан."
        )

    def test_create_report_for_inactive_user(self):
        """Тест на запрет создания отчёта для неактивного пользователя."""
        inactive_performer = User.objects.create_user(
            username="inactive_performer",
            email="inactive_performer@example.com",
            password="password",
            is_manager=False,
            is_active=False,
        )
        self.client.force_authenticate(user=inactive_performer)
        data = {"text": "Task report text"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
