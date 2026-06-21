from django.urls import path

from . import views

app_name = "meals"

urlpatterns = [
    path("issue/", views.IssueTokenView.as_view(), name="issue"),
    path("consume/", views.ConsumeTokenView.as_view(), name="consume"),
    path("today/", views.TodayTokensView.as_view(), name="today"),
    path("plans/", views.DailyMealPlanListView.as_view(), name="plans"),
    path("plans/add/", views.DailyMealPlanCreateView.as_view(), name="plan_add"),
]
