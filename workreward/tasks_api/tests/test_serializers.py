import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory


from tasks_api import serializers
from tasks_api.models import Task


User = get_user_model()


class TaskSerializerTests(TestCase):
    """Тесты для сериализатора UserSerializer."""

    def setUp(self):
        # Создаем тестового пользователя
        self.manager = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="testpassword123",
            is_manager=True,
        )
        self.task = Task.objects.create(
            title="task",
            description="desc",
            difficulty=3,
            task_duration=datetime.timedelta(minutes=30),
            task_creator=self.manager,
        )

        task_time_create = self.task.time_create.astimezone(
            timezone.get_current_timezone()
        )

        # Ожидаемое сериализованное представление
        self.expected_data = {
            "id": self.task.id,
            "title": "task",
            "description": "desc",
            "difficulty": 3,
            "task_duration": "00:30:00",
            "time_create": task_time_create.isoformat(),
            "time_completion": None,
            "time_start": None,
            "task_creator": "Doe John Smith",
            "task_performer": None,
        }

    def test_serialization(self):
        """Тест сериализации данных пользователя."""
        serializer = serializers.TaskSerializer(instance=self.task)
        self.assertEqual(serializer.data, self.expected_data)


class TaskCreateSerializerTests(TestCase):
    """Тесты для сериализатора TaskCreateSerializer."""

    def setUp(self):
        # Создаем тестовых пользователей
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="managerpassword123",
            is_manager=True,
        )
        self.active_performer = User.objects.create_user(
            username="performer_active",
            email="performer_active@example.com",
            first_name="Jane",
            last_name="Smith",
            patronymic="Alice",
            password="performerpassword123",
            is_manager=False,
            is_active=True,
        )
        self.inactive_performer = User.objects.create_user(
            username="performer_inactive",
            email="performer_inactive@example.com",
            first_name="Bob",
            last_name="Johnson",
            patronymic="Alex",
            password="performerpassword123",
            is_manager=False,
            is_active=False,
        )

    def _get_request_for_user(self, user):
        """Возвращает объект запроса для пользователя."""
        request = APIRequestFactory().post("test_url/", data={})
        request.user = user
        return request

    def test_create_task_success(self):
        """Тест успешного создания задачи с назначением исполнителя."""
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 3,
            "task_duration": "00:30:00",
            "task_performer": self.active_performer.id,
        }
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskCreateSerializer(
            data=data, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        task = serializer.save()

        # Проверяем, что задача создана корректно
        self.assertEqual(task.title, "New Task")
        self.assertEqual(task.description, "Task description")
        self.assertEqual(task.difficulty, 3)
        self.assertEqual(task.task_creator, self.manager)
        self.assertEqual(task.task_performer, self.active_performer)
        self.assertIsNotNone(task.time_start)

    def test_create_task_without_performer(self):
        """Тест создания задачи без назначения исполнителя."""
        data = {
            "title": "New Task Without Performer",
            "description": "Task description",
            "difficulty": 2,
            "task_duration": "00:30:00",
        }
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskCreateSerializer(
            data=data, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        task = serializer.save()

        # Проверяем, что задача создана корректно
        self.assertEqual(task.title, "New Task Without Performer")
        self.assertEqual(task.description, "Task description")
        self.assertEqual(task.difficulty, 2)
        self.assertEqual(task.task_creator, self.manager)
        self.assertIsNone(task.task_performer)
        self.assertIsNone(task.time_start)

    def test_create_task_invalid_performer_inactive(self):
        """Тест с неактивным исполнителем."""
        data = {
            "title": "New Task",
            "description": "Task description",
            "difficulty": 4,
            "task_duration": "01:00:00",
            "task_performer": self.inactive_performer.id,
        }
        request = self._get_request_for_user(self.inactive_performer)
        serializer = serializers.TaskCreateSerializer(
            data=data, context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_task_not_manager(self):
        """Тест с исполнителем, пытающимся создать задачу."""
        data = {
            "title": "Task by Non-manager",
            "description": "Task description",
            "difficulty": 2,
            "task_duration": "00:30:00",
        }
        request = self._get_request_for_user(self.active_performer)
        serializer = serializers.TaskCreateSerializer(
            data=data, context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class TaskTakeSerializerTests(TestCase):
    """Тесты для сериализатора TaskTakeSerializer."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="managerpassword123",
            is_manager=True,
        )
        self.active_performer = User.objects.create_user(
            username="performer_active",
            email="performer_active@example.com",
            first_name="Jane",
            last_name="Smith",
            patronymic="Alice",
            password="performerpassword123",
            is_manager=False,
            is_active=True,
        )
        self.task_without_performer = Task.objects.create(
            title="Task without performer",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
        )

        self.task_with_performer = Task.objects.create(
            title="Task with performer",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
            task_performer=self.active_performer,
        )

    def _get_request_for_user(self, user):
        """Возвращает объект запроса для пользователя."""
        request = APIRequestFactory().post("test_url/", data={})
        request.user = user
        return request

    def test_manager_cannot_take_task(self):
        """Тест с менеджером, пытающимся взять задачу."""
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskTakeSerializer(
            data={},
            instance=self.task_without_performer,
            context={"request": request},
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_task_with_performer_cannot_be_taken(self):
        """Тест с задачей, которая уже имеет исполнителя."""
        request = self._get_request_for_user(self.active_performer)
        serializer = serializers.TaskTakeSerializer(
            data={},
            instance=self.task_with_performer,
            context={"request": request},
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_task_taken_by_performer(self):
        """Тест с исполнителем, который может взять задачу."""
        request = self._get_request_for_user(self.active_performer)
        serializer = serializers.TaskTakeSerializer(
            data={},
            instance=self.task_without_performer,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()

        self.assertEqual(updated_task.task_performer, self.active_performer)
        self.assertIsNotNone(updated_task.time_start)

    def test_task_time_start_updated_when_taken(self):
        """Проверка, что время начала задачи обновляется при взятии задачи."""
        request = self._get_request_for_user(self.active_performer)
        serializer = serializers.TaskTakeSerializer(
            data={},
            instance=self.task_without_performer,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()

        self.assertIsNotNone(updated_task.time_start)
        self.assertEqual(updated_task.task_performer, self.active_performer)
        self.assertTrue(
            updated_task.time_start <= timezone.localtime(timezone.now())
        )


class TaskAssignSerializerTests(TestCase):
    """Тесты для сериализатора TaskAssignSerializer."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="managerpassword123",
            is_manager=True,
        )
        self.other_manager = User.objects.create_user(
            username="other_manager",
            email="other_manager@example.com",
            first_name="Alice",
            last_name="Johnson",
            patronymic="Smith",
            password="other_managerpassword123",
            is_manager=True,
        )
        self.active_performer = User.objects.create_user(
            username="performer_active",
            email="performer_active@example.com",
            first_name="Jane",
            last_name="Smith",
            patronymic="Alice",
            password="performerpassword123",
            is_manager=False,
            is_active=True,
        )
        self.inactive_performer = User.objects.create_user(
            username="performer_inactive",
            email="performer_inactive@example.com",
            first_name="Bob",
            last_name="Brown",
            patronymic="Charlie",
            password="performerpassword123",
            is_manager=False,
            is_active=False,
        )
        self.task_without_performer = Task.objects.create(
            title="Task without performer",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
        )
        self.task_with_performer = Task.objects.create(
            title="Task with performer",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
            task_performer=self.active_performer,
        )

    def _get_request_for_user(self, user):
        """Возвращает объект запроса для пользователя."""
        request = APIRequestFactory().post("test_url/", data={})
        request.user = user
        return request

    def test_manager_can_assign_task(self):
        """Менеджер должен быть в состоянии назначить исполнителя."""
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskAssignSerializer(
            instance=self.task_without_performer,
            data={"task_performer": self.active_performer.id},
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()

        self.assertEqual(updated_task.task_performer, self.active_performer)
        self.assertIsNotNone(updated_task.time_start)

    def test_only_manager_can_assign_task(self):
        """Только менеджер может назначать исполнителя."""
        request = self._get_request_for_user(self.active_performer)
        serializer = serializers.TaskAssignSerializer(
            instance=self.task_without_performer,
            data={"task_performer": self.active_performer.id},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_task_cannot_have_multiple_performers(self):
        """Невозможно назначить исполнителя, если задача уже имеет исполнителя."""
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskAssignSerializer(
            instance=self.task_with_performer,
            data={"task_performer": self.active_performer.id},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_assign_inactive_performer(self):
        """Невозможно назначить неактивного исполнителя."""
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskAssignSerializer(
            instance=self.task_without_performer,
            data={"task_performer": self.inactive_performer.id},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_task_creator_is_manager(self):
        """Только создатель задачи (менеджер) может назначить исполнителя."""
        request = self._get_request_for_user(self.other_manager)
        serializer = serializers.TaskAssignSerializer(
            instance=self.task_without_performer,
            data={"task_performer": self.active_performer.id},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class TaskCompleteSerializerTests(TestCase):
    """Тесты для сериализатора TaskCompleteSerializer."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            first_name="John",
            last_name="Doe",
            patronymic="Smith",
            password="managerpassword123",
            is_manager=True,
        )
        self.performer = User.objects.create_user(
            username="performer",
            email="performer@example.com",
            first_name="Jane",
            last_name="Smith",
            patronymic="Alice",
            password="performerpassword123",
            is_manager=False,
            is_active=True,
        )
        self.other_performer = User.objects.create_user(
            username="other_performer",
            email="other_performer@example.com",
            first_name="Bob",
            last_name="Brown",
            patronymic="Charlie",
            password="other_performerpassword123",
            is_manager=False,
            is_active=True,
        )

        self.task_not_completed = Task.objects.create(
            title="Task not completed",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
            task_performer=self.performer,
        )
        self.task_completed = Task.objects.create(
            title="Task completed",
            description="Task description",
            difficulty=3,
            task_duration="00:30:00",
            task_creator=self.manager,
            task_performer=self.performer,
            time_completion=timezone.localtime(timezone.now())
        )

    def _get_request_for_user(self, user):
        """Возвращает объект запроса для пользователя."""
        request = APIRequestFactory().post("test_url/", data={})
        request.user = user
        return request

    def test_performer_can_complete_task(self):
        """Исполнитель должен быть в состоянии завершить задачу."""
        request = self._get_request_for_user(self.performer)
        serializer = serializers.TaskCompleteSerializer(
            instance=self.task_not_completed,
            data={},
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        self.assertIsNotNone(updated_task.time_completion)

    def test_manager_cannot_complete_task(self):
        """Менеджер не может завершить задачу."""
        request = self._get_request_for_user(self.manager)
        serializer = serializers.TaskCompleteSerializer(
            instance=self.task_not_completed,
            data={},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_other_performer_cannot_complete_task(self):
        """Другой исполнитель не может завершить задачу."""
        request = self._get_request_for_user(self.other_performer)
        serializer = serializers.TaskCompleteSerializer(
            instance=self.task_not_completed,
            data={},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_task_cannot_be_completed_twice(self):
        """Задача не может быть завершена дважды."""
        request = self._get_request_for_user(self.performer)
        serializer = serializers.TaskCompleteSerializer(
            instance=self.task_completed,
            data={},
            context={"request": request}
        )
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
