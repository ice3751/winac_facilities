from django.urls import path

from . import views

app_name = "people"

urlpatterns = [
    path("", views.PersonnelListView.as_view(), name="list"),
    path("add/", views.PersonnelCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.PersonnelUpdateView.as_view(), name="edit"),
]
