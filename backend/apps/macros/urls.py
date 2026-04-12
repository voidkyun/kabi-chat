from django.urls import path

from .views import MacroListView


urlpatterns = [
    path("", MacroListView.as_view(), name="macro-list"),
]
