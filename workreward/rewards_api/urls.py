from django.urls import path

from . import views

app_name = "rewards_api"
urlpatterns = [
    path(
        "<int:report_pk>/create/",
        views.RewardCreateAPIView.as_view(),
        name="reward_create",
    ),
    path(
        "my-rewards/",
        views.RewardViewSet.as_view({"get": "list"}),
        name="user_rewards",
    ),
]
