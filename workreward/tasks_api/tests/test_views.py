import datetime
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tasks_api.models import Task

User = get_user_model()


class TaskViewSetTests(APITestCase):
    """Тесты для TaskViewSet."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="KKKKK12345",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="KKKKK12345",
            is_manager=False,
        )

        cls.task_without_performer = Task.objects.create(
            title="Task without Performer",
            difficulty=3,
            task_duration=datetime.timedelta(minutes=30),
            task_creator=cls.manager,
            task_performer=None,
        )
        cls.task_with_performer = Task.objects.create(
            title="Task with Performer",
            difficulty=3,
            task_duration=datetime.timedelta(minutes=30),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )

    def test_tasks_list_access_for_manager(self):
        """
        Тест на возможность доступа менеджера к списку задач.
        Менеджер должен видеть только назначенные им задачи.
        """
        self.client.force_authenticate(user=self.manager)
        url = reverse("tasks_api:tasks_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_detail_task_access_for_manager(self):
        """
        Тест на возможность доступа менеджера к информации о задаче.
        Менеджер должен видеть только назначенные им задачи.
        """
        self.client.force_authenticate(user=self.manager)
        url = reverse(
            "tasks_api:task_detail",
            kwargs={"pk": self.task_without_performer.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task_without_performer.pk)

    def test_tasks_list_access_for_performer(self):
        """
        Тест на возможность доступа исполнителя
        к списку задач. Исполнитель должен видеть
        только задачи, не имеющие исполнителя.
        """
        self.client.force_authenticate(user=self.performer)
        url = reverse("tasks_api:tasks_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_detail_free_task_access_for_performer(self):
        """
        Тест на возможность доступа исполнителя
        к информации о свободной задаче.
        Исполнитель видеть задачи без исполнителя.
        """
        self.client.force_authenticate(user=self.performer)
        url = reverse(
            "tasks_api:task_detail",
            kwargs={"pk": self.task_without_performer.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task_without_performer.pk)

    def test_detail_assigned_task_access_for_performer(self):
        """
        Тест на возможность доступа исполнителя
        к информации о задаче задаче. Исполнитель
        не должен видеть задачи с назначенным исполнителем.
        """
        self.client.force_authenticate(user=self.performer)
        url = reverse(
            "tasks_api:task_detail", kwargs={"pk": self.task_with_performer.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tasks_list_access_for_unauthenticated_user(self):
        """
        Тест на невозможность доступа
        неаутентифицированного пользователя к списку задач.
        """
        url = reverse("tasks_api:tasks_list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_task_access_for_unauthenticated_user(self):
        """
        Тест на невозможность доступа
        неаутентифицированного пользователя к задаче.
        """
        url = reverse(
            "tasks_api:task_detail",
            kwargs={"pk": self.task_without_performer.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserTasksAPIViewTests(APITestCase):
    """Тесты для UserTasksAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("tasks_api:user_tasks")

        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="KKKKK12345",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="KKKKK12345",
            is_manager=False,
        )

        cls.task1 = Task.objects.create(
            title="Task 1",
            difficulty=3,
            task_duration=datetime.timedelta(minutes=30),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )
        cls.task2 = Task.objects.create(
            title="Task 2",
            difficulty=2,
            task_duration=datetime.timedelta(minutes=20),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )
        cls.task3 = Task.objects.create(
            title="Task 3",
            difficulty=1,
            task_duration=datetime.timedelta(minutes=10),
            task_creator=cls.manager,
            task_performer=cls.performer,
        )

    def test_get_tasks_for_performer(self):
        """Тест для получения задач исполнителя."""
        self.client.force_authenticate(user=self.performer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_get_tasks_for_manager(self):
        """Тест на запрет доступа для менеджера."""

        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_authenticated_user_access(self):
        """
        Тест на невозможность доступа
        неаутентифицированного пользователя.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskCreateAPIViewTests(APITestCase):
    """Тесты для TaskCreateAPIView."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("tasks_api:create_task")

        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="KKKKK12345",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="KKKKK12345",
            is_manager=False,
        )
        cls.inactive_performer = User.objects.create_user(
            username="inactive_performer",
            email="inactive_performer@example.com",
            password="KKKKK12345",
            is_manager=False,
            is_active=False,
        )

    def test_create_task_as_manager(self):
        """Тест для создания задачи менеджером."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 3,
            "task_duration": "01:00:00",
            "task_performer": self.performer.id,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data["title"], "New Task")
        self.assertEqual(response.data["description"], "Task description")
        self.assertEqual(response.data["difficulty"], 3)
        self.assertEqual(response.data["task_duration"], "01:00:00")
        self.assertEqual(response.data["task_creator"], self.manager.id)
        self.assertEqual(response.data["task_performer"], self.performer.id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.performer.email, mail.outbox[0].to)

    def test_create_task_as_non_manager(self):
        """Тест на запрет создания задачи не менеджером."""
        self.client.force_authenticate(user=self.performer)
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 3,
            "task_duration": "01:00:00",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_task_with_inactive_performer(self):
        """Тест на валидацию неактивного исполнителя."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 3,
            "task_duration": "01:00:00",
            "task_performer": self.inactive_performer.id,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["task_performer"]["task_performer"],
            "Назначенный пользователь неактивен.",
        )

    def test_create_task_without_performer(self):
        """Тест на создание задачи без исполнителя."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 3,
            "task_duration": "01:00:00",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["task_performer"])

    def test_create_task_missing_fields(self):
        """Тест на пропущенные обязательные поля при создании задачи."""
        self.client.force_authenticate(user=self.manager)
        data = {
            "title": "New Task",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)
        self.assertIn("difficulty", response.data)
        self.assertIn("task_duration", response.data)


class TaskTakeAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="KKKKK12345",
            is_manager=True,
        )
        cls.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            password="KKKKK12345",
            is_manager=False,
        )

        cls.task = Task.objects.create(
            title="Test Task",
            description="Test Task Description",
            difficulty=3,
            task_duration="02:00:00",
            task_creator=cls.manager,
        )

        cls.url = reverse("tasks_api:task_take", kwargs={"pk": cls.task.pk})

    def test_successful_task_take(self):
        """Тест на успешное взятие задачи исполнителем."""
        self.client.force_authenticate(user=self.performer)

        response = self.client.patch(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            f"Вы успешно взяли задачу с id: {self.task.pk}.",
        )

        self.task.refresh_from_db()
        self.assertEqual(self.task.task_performer, self.performer)
        self.assertIsNotNone(self.task.time_start)

    def test_task_take_by_manager(self):
        """Тест на попытку менеджера взять задачу."""
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_already_taken(self):
        """Тест на попытку взять задачу, которая уже имеет исполнителя."""
        self.task.task_performer = self.performer
        self.task.save()
        self.client.force_authenticate(user=self.performer)

        response = self.client.patch(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0], "Задача уже имеет исполнителя."
        )

    def test_nonexistent_task(self):
        """Тест на попытку взять несуществующую задачу."""
        nonexistent_url = reverse("tasks_api:task_take", kwargs={"pk": 9999})
        self.client.force_authenticate(user=self.performer)
        response = self.client.patch(nonexistent_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskAssignAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password",
            is_manager=True,
        )
        cls.other_manager = User.objects.create_user(
            username="other_manager",
            email="other_manager@example.com",
            password="password",
            is_manager=True,
        )
        cls.active_performer = User.objects.create_user(
            username="active_performer",
            email="active_performer@example.com",
            password="password",
            is_manager=False,
            is_active=True,
        )
        cls.inactive_performer = User.objects.create_user(
            username="inactive_performer",
            email="inactive_performer@example.com",
            password="password",
            is_manager=False,
            is_active=False,
        )

        cls.task = Task.objects.create(
            title="Test Task",
            description="Test Task Description",
            difficulty=3,
            task_duration="02:00:00",
            task_creator=cls.manager,
        )
        cls.url = reverse("tasks_api:task_assign", kwargs={"pk": cls.task.pk})

    def test_successful_task_assignment(self):
        """
        Тест на успешное назначение задачи
        активному исполнителю менеджером.
        """
        self.client.force_authenticate(user=self.manager)
        data = {"task_performer": self.active_performer.pk}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()
        self.assertEqual(self.task.task_performer, self.active_performer)
        self.assertIsNotNone(self.task.time_start)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.active_performer.email, mail.outbox[0].to)

    def test_task_assignment_by_non_manager(self):
        """Тест на попытку назначения задачи не-менеджером."""
        self.client.force_authenticate(user=self.active_performer)
        data = {"task_performer": self.active_performer.pk}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_assignment_by_other_manager(self):
        """Тест на попытку назначения задачи другим менеджером."""
        self.client.force_authenticate(user=self.other_manager)
        data = {"task_performer": self.active_performer.pk}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Вы не можете назначать исполнителей на задачи другого менеджера.",
        )

    def test_task_assignment_to_inactive_performer(self):
        """Тест на попытку назначения задачи неактивному исполнителю."""
        self.client.force_authenticate(user=self.manager)
        data = {"task_performer": self.inactive_performer.pk}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["task_performer"]["task_performer"],
            "Назначенный пользователь неактивен.",
        )

    def test_task_already_has_performer(self):
        """Тест на попытку назначения задачи, которая уже имеет исполнителя."""
        self.task.task_performer = self.active_performer
        self.task.save()
        self.client.force_authenticate(user=self.manager)
        data = {"task_performer": self.active_performer.pk}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0], "Задача уже имеет исполнителя."
        )

    def test_nonexistent_task_assignment(self):
        """Тест на попытку назначения несуществующей задачи."""
        nonexistent_url = reverse("tasks_api:task_assign", kwargs={"pk": 9999})
        self.client.force_authenticate(user=self.manager)
        data = {"task_performer": self.active_performer.pk}

        response = self.client.patch(nonexistent_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskCompleteAPIViewTestCase(APITestCase):
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
        cls.other_user = User.objects.create_user(
            username="other_user",
            email="other_user@example.com",
            password="password",
            is_manager=False,
        )

        cls.task = Task.objects.create(
            title="Test Task",
            description="Test Task Description",
            difficulty=3,
            task_duration="02:00:00",
            task_creator=cls.manager,
            task_performer=cls.performer,
        )
        cls.url = reverse(
            "tasks_api:task_complete", kwargs={"pk": cls.task.pk}
        )

    def test_successful_task_completion(self):
        """
        Тест на успешное завершение задачи исполнителем.
        """
        self.client.force_authenticate(user=self.performer)

        response = self.client.patch(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.time_completion)

    def test_task_completion_by_manager(self):
        """
        Тест на попытку завершения задачи менеджером.
        """
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_completion_by_other_user(self):
        """
        Тест на попытку завершения задачи
        другим пользователем (не исполнителем).
        """
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Вы не являетесь исполнителем этой задачи.",
        )

    def test_completion_of_already_completed_task(self):
        """
        Тест на попытку завершения уже завершенной задачи.
        """
        self.task.time_completion = timezone.localtime(timezone.now())
        self.task.save()

        self.client.force_authenticate(user=self.performer)

        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Эта задача уже завершена."
        )

    def test_nonexistent_task_completion(self):
        """
        Тест на попытку завершения несуществующей задачи.
        """
        nonexistent_url = reverse(
            "tasks_api:task_complete", kwargs={"pk": 9999}
        )
        self.client.force_authenticate(user=self.performer)

        response = self.client.patch(nonexistent_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
