from django.urls import path

from .views import (
    WorkspaceDetailView,
    WorkspaceInviteAcceptView,
    WorkspaceInviteCreateView,
    WorkspaceListCreateView,
)


urlpatterns = [
    path("", WorkspaceListCreateView.as_view(), name="workspace-list"),
    path("invites/accept/", WorkspaceInviteAcceptView.as_view(), name="workspace-invite-accept"),
    path("<int:pk>/invites/", WorkspaceInviteCreateView.as_view(), name="workspace-invite-create"),
    path("<int:pk>/", WorkspaceDetailView.as_view(), name="workspace-detail"),
]
