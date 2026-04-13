from django.urls import path

from .views import MacroDetailView, MacroListCreateView


urlpatterns = [
    path("", MacroListCreateView.as_view(), name="macro-list"),
    path("<int:pk>/", MacroDetailView.as_view(), name="macro-detail"),
]
