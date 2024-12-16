from django.urls import path

from . import views

app_name = "tasks_api"
urlpatterns = [
    path(
        "create/",
        views.TaskCreateAPIView.as_view(),
        name="create_task",
    ),
    path(
        "list/",
        views.TaskViewSet.as_view({"get": "list"}),
        name="tasks_list",
    ),
    path(
        "list/<int:pk>/",
        views.TaskViewSet.as_view({"get": "retrieve"}),
        name="task_detail",
    ),
    path(
        "list/<int:pk>/take/",
        views.TaskTakeAPIView.as_view(),
        name="task_take",
    ),
    path(
        "list/<int:pk>/assign/",
        views.TaskAssignAPIView.as_view(),
        name="task_assign",
    ),
    path(
        "list/<int:pk>/complete/",
        views.TaskCompleteAPIView.as_view(),
        name="task_complete",
    ),
    path(
        "my-tasks/",
        views.UserTasksAPIView.as_view(),
        name="user_tasks",
    ),
]
