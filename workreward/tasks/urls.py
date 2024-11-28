from django.urls import path
from tasks import views

app_name = "tasks"

urlpatterns = [
    path("", views.index, name="home"),
    path("about/", views.about, name="about"),
    path("tasks/", views.tasks, name="tasks"),
]
