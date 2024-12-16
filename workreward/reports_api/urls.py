from django.urls import path

from . import views

app_name = "reports_api"
urlpatterns = [
    path(
        "<int:task_pk>/create/",
        views.TaskReportCreateAPIView.as_view(),
        name="report_create",
    ),
    path(
        "list/",
        views.TaskReportViewSet.as_view({"get": "list"}),
        name="report_list",
    ),
    path(
        "list/<int:pk>/",
        views.TaskReportViewSet.as_view({"get": "retrieve"}),
        name="report_detail",
    ),
]
