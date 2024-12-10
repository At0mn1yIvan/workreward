from django.urls import path

from .views import TaskCreateAPIView, TaskDetailAPIView, TaskListAPIView

app_name = "tasks_api"
urlpatterns = [
    path(
        "create/",
        TaskCreateAPIView.as_view(),
        name="create_task",
    ),
    path(
        "<int:task_id>/",
        TaskDetailAPIView.as_view(),
        name="task_detal",
    ),
    path(
        "list/",
        TaskListAPIView.as_view(),
        name="tasks_list",
    ),
]
