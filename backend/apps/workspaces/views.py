from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import generics

from .models import Workspace
from .permissions import IsWorkspaceMemberOrManager
from .serializers import WorkspaceSerializer


class WorkspaceListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        user_model = get_user_model()
        return (
            Workspace.objects.accessible_to(self.request.user)
            .select_related("owner", "owner__auth_profile")
            .prefetch_related(
                Prefetch(
                    "members",
                    queryset=user_model.objects.select_related("auth_profile"),
                ),
                "workspace_memberships",
            )
        )


class WorkspaceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsWorkspaceMemberOrManager]

    def get_queryset(self):
        user_model = get_user_model()
        return (
            Workspace.objects.accessible_to(self.request.user)
            .select_related("owner", "owner__auth_profile")
            .prefetch_related(
                Prefetch(
                    "members",
                    queryset=user_model.objects.select_related("auth_profile"),
                ),
                "workspace_memberships",
            )
        )
