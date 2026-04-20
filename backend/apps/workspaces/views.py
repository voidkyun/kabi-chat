from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Workspace, WorkspaceMembership
from .permissions import IsWorkspaceMemberOrManager
from .serializers import WorkspaceInviteSerializer, WorkspaceSerializer
from .services import find_workspace_invite_by_token, issue_workspace_invite


def workspace_queryset_for(user):
    user_model = get_user_model()
    return (
        Workspace.objects.accessible_to(user)
        .select_related("owner", "owner__auth_profile")
        .prefetch_related(
            Prefetch(
                "members",
                queryset=user_model.objects.select_related("auth_profile"),
            ),
            "workspace_memberships",
        )
    )


class WorkspaceListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return workspace_queryset_for(self.request.user)


class WorkspaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsWorkspaceMemberOrManager]

    def get_queryset(self):
        return workspace_queryset_for(self.request.user)


class WorkspaceInviteCreateView(APIView):
    def post(self, request, pk):
        workspace = workspace_queryset_for(request.user).filter(pk=pk).first()
        if workspace is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if not workspace.can_manage(request.user):
            raise PermissionDenied("Only workspace owners can create invites.")

        invite, token = issue_workspace_invite(workspace=workspace, created_by=request.user)
        payload = WorkspaceInviteSerializer(invite).data
        payload["invite_token"] = token
        return Response(payload, status=status.HTTP_201_CREATED)


class WorkspaceInviteAcceptView(APIView):
    def post(self, request):
        raw_token = request.data.get("token", "")
        token = raw_token.strip() if isinstance(raw_token, str) else ""
        if not token:
            return Response(
                {"detail": "Invite token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            invite = find_workspace_invite_by_token(token, for_update=True)
            if invite is None:
                return Response(
                    {"detail": "Invite token is invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if invite.is_expired():
                return Response(
                    {"detail": "This invite has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            workspace = invite.workspace
            if workspace.has_member(request.user):
                joined = False
            else:
                if invite.is_consumed():
                    return Response(
                        {"detail": "This invite has already been used."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                WorkspaceMembership.objects.create(
                    workspace=workspace,
                    user=request.user,
                    role=WorkspaceMembership.Role.MEMBER,
                )
                invite.accepted_by = request.user
                invite.accepted_at = timezone.now()
                invite.save(update_fields=["accepted_by", "accepted_at"])
                joined = True

        serialized_workspace = WorkspaceSerializer(
            workspace_queryset_for(request.user).get(pk=workspace.pk),
            context={"request": request},
        ).data
        return Response(
            {
                "joined": joined,
                "workspace": serialized_workspace,
            }
        )
