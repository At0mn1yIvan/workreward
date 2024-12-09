from django.urls import path

from .views import TaskCreateAPIView


app_name = "tasks_api"
urlpatterns = [
    path(
        "create/",
        TaskCreateAPIView.as_view(),
        name="create_task",
    )
]
