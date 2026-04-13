import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Workspace, WorkspaceMembership


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
