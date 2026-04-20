from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Workspace, WorkspaceInvite, WorkspaceMembership


def create_workspace(*, owner, name="Algebra", description=""):
    workspace = Workspace.objects.create(name=name, description=description, owner=owner)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=owner,
        role=WorkspaceMembership.Role.OWNER,
    )
    return workspace


def add_member(workspace, user):
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.MEMBER,
    )


@pytest.fixture
def authenticated_clients():
    user_model = get_user_model()
    owner = user_model.objects.create_user(username="owner", password="password123")
    member = user_model.objects.create_user(username="member", password="password123")
    outsider = user_model.objects.create_user(username="outsider", password="password123")

    def build_client(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return {
        "owner": (build_client(owner), owner),
        "member": (build_client(member), member),
        "outsider": (build_client(outsider), outsider),
    }


@pytest.mark.django_db
def test_workspace_crud_respects_membership_and_manager_permissions(authenticated_clients):
    owner_client, owner = authenticated_clients["owner"]
    member_client, member = authenticated_clients["member"]
    outsider_client, outsider = authenticated_clients["outsider"]

    create_response = owner_client.post(
        reverse("workspace-list"),
        {
            "name": "Calculus",
            "description": "Notes",
            "member_ids": [member.id],
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    workspace_id = create_response.json()["id"]
    payload = create_response.json()
    assert payload["owner"]["id"] == owner.id
    assert sorted(payload["member_ids"]) == [owner.id, member.id]

    list_response = member_client.get(reverse("workspace-list"))
    assert list_response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in list_response.json()] == [workspace_id]

    detail_response = outsider_client.get(reverse("workspace-detail", args=[workspace_id]))
    assert detail_response.status_code == status.HTTP_404_NOT_FOUND

    member_patch_response = member_client.patch(
        reverse("workspace-detail", args=[workspace_id]),
        {"description": "Updated by member"},
        format="json",
    )
    assert member_patch_response.status_code == status.HTTP_403_FORBIDDEN

    owner_patch_response = owner_client.patch(
        reverse("workspace-detail", args=[workspace_id]),
        {
            "description": "Updated by owner",
            "member_ids": [],
        },
        format="json",
    )
    assert owner_patch_response.status_code == status.HTTP_200_OK
    assert owner_patch_response.json()["description"] == "Updated by owner"
    assert owner_patch_response.json()["member_ids"] == [owner.id]

    workspace = Workspace.objects.get(pk=workspace_id)
    assert workspace.workspace_memberships.filter(user=member).count() == 0
    assert workspace.workspace_memberships.filter(user=outsider).count() == 0

    member_delete_response = member_client.delete(reverse("workspace-detail", args=[workspace_id]))
    assert member_delete_response.status_code == status.HTTP_404_NOT_FOUND

    owner_delete_response = owner_client.delete(reverse("workspace-detail", args=[workspace_id]))
    assert owner_delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert Workspace.objects.filter(pk=workspace_id).count() == 0


@pytest.mark.django_db
def test_workspace_list_only_returns_accessible_workspaces(authenticated_clients):
    owner_client, owner = authenticated_clients["owner"]
    member_client, member = authenticated_clients["member"]

    workspace = create_workspace(owner=owner, name="Topology")
    add_member(workspace, member)

    owner_list = owner_client.get(reverse("workspace-list"))
    member_list = member_client.get(reverse("workspace-list"))

    assert [item["id"] for item in owner_list.json()] == [workspace.id]
    assert [item["id"] for item in member_list.json()] == [workspace.id]


@pytest.mark.django_db
def test_workspace_invite_allows_single_use_join(authenticated_clients):
    owner_client, owner = authenticated_clients["owner"]
    member_client, member = authenticated_clients["member"]
    outsider_client, outsider = authenticated_clients["outsider"]

    workspace = create_workspace(owner=owner, name="Invites")

    create_invite_response = owner_client.post(
        reverse("workspace-invite-create", args=[workspace.id]),
        format="json",
    )

    assert create_invite_response.status_code == status.HTTP_201_CREATED
    invite_payload = create_invite_response.json()
    invite = WorkspaceInvite.objects.get(pk=invite_payload["id"])
    assert invite.created_by_id == owner.id
    assert invite.accepted_at is None
    assert invite_payload["invite_token"]

    member_accept_response = member_client.post(
        reverse("workspace-invite-accept"),
        {"token": invite_payload["invite_token"]},
        format="json",
    )
    assert member_accept_response.status_code == status.HTTP_200_OK
    assert member_accept_response.json()["joined"] is True
    assert member_accept_response.json()["workspace"]["id"] == workspace.id
    assert workspace.workspace_memberships.filter(user=member).count() == 1

    invite.refresh_from_db()
    assert invite.accepted_by_id == member.id
    assert invite.accepted_at is not None

    owner_accept_response = owner_client.post(
        reverse("workspace-invite-accept"),
        {"token": invite_payload["invite_token"]},
        format="json",
    )
    assert owner_accept_response.status_code == status.HTTP_200_OK
    assert owner_accept_response.json()["joined"] is False

    outsider_accept_response = outsider_client.post(
        reverse("workspace-invite-accept"),
        {"token": invite_payload["invite_token"]},
        format="json",
    )
    assert outsider_accept_response.status_code == status.HTTP_400_BAD_REQUEST
    assert outsider_accept_response.json() == {"detail": "This invite has already been used."}
    assert workspace.workspace_memberships.filter(user=outsider).count() == 0


@pytest.mark.django_db
def test_workspace_invite_rejects_invalid_or_expired_tokens(authenticated_clients):
    owner_client, owner = authenticated_clients["owner"]
    outsider_client, outsider = authenticated_clients["outsider"]

    workspace = create_workspace(owner=owner, name="Expiring")

    invalid_response = outsider_client.post(
        reverse("workspace-invite-accept"),
        {"token": "invalid-token"},
        format="json",
    )
    assert invalid_response.status_code == status.HTTP_400_BAD_REQUEST
    assert invalid_response.json() == {"detail": "Invite token is invalid."}

    create_invite_response = owner_client.post(
        reverse("workspace-invite-create", args=[workspace.id]),
        format="json",
    )
    invite = WorkspaceInvite.objects.get(pk=create_invite_response.json()["id"])
    invite.expires_at = timezone.now() - timedelta(minutes=1)
    invite.save(update_fields=["expires_at"])

    expired_response = outsider_client.post(
        reverse("workspace-invite-accept"),
        {"token": create_invite_response.json()["invite_token"]},
        format="json",
    )
    assert expired_response.status_code == status.HTTP_400_BAD_REQUEST
    assert expired_response.json() == {"detail": "This invite has expired."}
    assert workspace.workspace_memberships.filter(user=outsider).count() == 0


@pytest.mark.django_db
def test_workspace_invite_creation_requires_workspace_ownership(authenticated_clients):
    owner_client, owner = authenticated_clients["owner"]
    member_client, member = authenticated_clients["member"]
    outsider_client, outsider = authenticated_clients["outsider"]

    workspace = create_workspace(owner=owner, name="Permissions")
    add_member(workspace, member)

    member_response = member_client.post(reverse("workspace-invite-create", args=[workspace.id]))
    outsider_response = outsider_client.post(reverse("workspace-invite-create", args=[workspace.id]))

    assert member_response.status_code == status.HTTP_403_FORBIDDEN
    assert member_response.json() == {"detail": "Only workspace owners can create invites."}
    assert outsider_response.status_code == status.HTTP_404_NOT_FOUND
