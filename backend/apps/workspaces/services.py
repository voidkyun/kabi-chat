import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import WorkspaceInvite


def hash_workspace_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_workspace_invite(*, workspace, created_by) -> tuple[WorkspaceInvite, str]:
    while True:
        token = secrets.token_urlsafe(24)
        token_digest = hash_workspace_invite_token(token)
        if not WorkspaceInvite.objects.filter(token_digest=token_digest).exists():
            break

    invite = WorkspaceInvite.objects.create(
        workspace=workspace,
        created_by=created_by,
        token_digest=token_digest,
        expires_at=timezone.now() + timedelta(seconds=settings.WORKSPACE_INVITE_TTL_SECONDS),
    )
    return invite, token


def find_workspace_invite_by_token(token: str, *, for_update: bool = False) -> WorkspaceInvite | None:
    token_digest = hash_workspace_invite_token(token)
    queryset = WorkspaceInvite.objects.select_related(
            "workspace",
            "workspace__owner",
            "workspace__owner__auth_profile",
            "created_by",
            "created_by__auth_profile",
            "accepted_by",
            "accepted_by__auth_profile",
        )
    if for_update:
        queryset = queryset.select_for_update(of=("self",))
    return queryset.filter(token_digest=token_digest).first()
