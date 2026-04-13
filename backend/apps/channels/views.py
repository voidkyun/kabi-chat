from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Channel
from .permissions import IsChannelWorkspaceMemberOrManager
from .serializers import ChannelSerializer


class ChannelListCreateView(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer

    def _parse_workspace_id(self):
        workspace_id = self.request.query_params.get("workspace_id")
        if workspace_id is None:
            return None
        try:
            return int(workspace_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"workspace_id": "Must be an integer."}) from exc

    def get_queryset(self):
        queryset = (
            Channel.objects.accessible_to(self.request.user)
            .select_related(
                "workspace",
                "workspace__owner",
                "workspace__owner__auth_profile",
                "created_by",
                "created_by__auth_profile",
            )
        )
        workspace_id = self._parse_workspace_id()
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChannelDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [IsChannelWorkspaceMemberOrManager]

    def get_queryset(self):
        return (
            Channel.objects.accessible_to(self.request.user)
            .select_related(
                "workspace",
                "workspace__owner",
                "workspace__owner__auth_profile",
                "created_by",
                "created_by__auth_profile",
            )
        )
