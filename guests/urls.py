from django.urls import path

from . import views

app_name = "guests"

urlpatterns = [
    path("", views.GuestListView.as_view(), name="list"),
    path("add/", views.GuestCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.GuestUpdateView.as_view(), name="edit"),

    path("cards/", views.GuestCardListView.as_view(), name="cards"),
    path("cards/add/", views.GuestCardCreateView.as_view(), name="card_add"),
    path("cards/<int:pk>/edit/", views.GuestCardUpdateView.as_view(), name="card_edit"),

    path("assignments/", views.CardAssignmentListView.as_view(), name="assignments"),
    path("assignments/add/", views.CardAssignmentCreateView.as_view(), name="assignment_add"),
    path("assignments/<int:pk>/edit/", views.CardAssignmentUpdateView.as_view(), name="assignment_edit"),
]
