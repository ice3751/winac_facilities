from django.urls import path

from . import views

app_name = "catering"

urlpatterns = [
    path("", views.CateringRequestListView.as_view(), name="list"),
    path("add/", views.CateringRequestCreateView.as_view(), name="add"),
    path("<int:pk>/", views.CateringRequestDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.CateringRequestUpdateView.as_view(), name="edit"),
    path("<int:pk>/add-item/", views.CateringRequestAddItemView.as_view(), name="add_item"),
    path("<int:pk>/item/<int:item_pk>/delete/", views.CateringRequestDeleteItemView.as_view(), name="delete_item"),
    path("<int:pk>/status/", views.CateringRequestSetStatusView.as_view(), name="set_status"),

    path("items/", views.CateringItemListView.as_view(), name="items"),
    path("items/add/", views.CateringItemCreateView.as_view(), name="item_add"),
    path("items/<int:pk>/edit/", views.CateringItemUpdateView.as_view(), name="item_edit"),

    path("locations/", views.CateringLocationListView.as_view(), name="locations"),
    path("locations/add/", views.CateringLocationCreateView.as_view(), name="location_add"),
    path("locations/<int:pk>/edit/", views.CateringLocationUpdateView.as_view(), name="location_edit"),

    path("supply/", views.SupplyPanelView.as_view(), name="supply"),
    path("supply/<int:item_pk>/purchased/", views.SupplyMarkPurchasedView.as_view(), name="supply_purchased"),
]
