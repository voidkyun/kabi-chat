from django.urls import path

from .views import WorkspaceListView


urlpatterns = [
    path("", WorkspaceListView.as_view(), name="workspace-list"),
]
