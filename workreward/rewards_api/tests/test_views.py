import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tasks_api.models import Task
from reports_api.models import TaskReport
from rewards_api.models import Reward

User = get_user_model()


class RewardViewSetTests(APITestCase):
    """Тесты для RewardViewSet."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("rewards_api:user_rewards")

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

        cls.task_report = TaskReport.objects.create(
            text="Test report text",
            efficiency_score=4.5,
            is_awarded=True,
            task=cls.task,
        )

        cls.reward = Reward.objects.create(
            reward_sum=100.00,
            comment="Test reward comment",
            task_report=cls.task_report,
        )

    def test_list_rewards_for_performer(self):
        """
        Тест на получение списка вознаграждений для исполнителя.
        Исполнитель должен видеть только вознаграждения по своим задачам.
        """
        self.client.force_authenticate(user=self.performer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_rewards_for_unauthenticated_user(self):
        """
        Тест на невозможность получения списка вознаграждений
        неаутентифицированным пользователем.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RewardCreateAPIViewTests(APITestCase):
    """Тесты для RewardCreateAPIView."""

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

        cls.task_report = TaskReport.objects.create(
            text="Test report text",
            efficiency_score=4.5,
            is_awarded=False,
            task=cls.task,
        )

        cls.url = reverse(
            "rewards_api:reward_create",
            kwargs={"report_pk": cls.task_report.pk},
        )

    def test_create_reward_as_manager(self):
        """Тест на создание вознаграждения менеджером."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "comment": "Excellent performance",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reward.objects.count(), 1)

        reward = Reward.objects.first()
        self.assertEqual(reward.reward_sum, Decimal("2250.00"))
        self.assertEqual(reward.comment, data["comment"])
        self.assertEqual(reward.task_report, self.task_report)

        self.task_report.refresh_from_db()
        self.assertTrue(self.task_report.is_awarded)

    def test_create_reward_as_non_manager(self):
        """
        Тест на создание вознаграждения
        не менеджером (должен вернуть ошибку).
        """
        self.client.force_authenticate(user=self.performer)
        data = {
            "comment": "Good performance",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reward_for_already_awarded_task(self):
        """
        Тест на попытку выдать вознаграждение
        для уже награжденной задачи.
        """
        self.task_report.is_awarded = True
        self.task_report.save()

        self.client.force_authenticate(user=self.manager)
        data = {
            "comment": "Good performance",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"][0], "Премия за эту задачу уже выдана."
        )

    def test_create_reward_with_high_efficiency_score(self):
        """
        Тест на создание вознаграждения при
        очень высокой эффективности (превышает лимит).
        """
        self.task_report.efficiency_score = 25
        self.task_report.save()

        self.client.force_authenticate(user=self.manager)
        data = {
            "comment": "Outstanding performance",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reward = Reward.objects.first()
        self.assertEqual(reward.reward_sum, Decimal("10000.00"))
