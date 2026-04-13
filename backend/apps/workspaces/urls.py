from django.urls import path

from .views import WorkspaceDetailView, WorkspaceListCreateView


urlpatterns = [
    path("", WorkspaceListCreateView.as_view(), name="workspace-list"),
    path("<int:pk>/", WorkspaceDetailView.as_view(), name="workspace-detail"),
]
