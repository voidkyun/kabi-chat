import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.channels.models import Channel
from apps.workspaces.models import Workspace, WorkspaceMembership

from .models import MacroDefinition


def create_workspace(*, owner):
    workspace = Workspace.objects.create(name="Macros", owner=owner)
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


def create_channel(*, workspace, created_by):
    return Channel.objects.create(
        workspace=workspace,
        name="macros",
        topic="",
        created_by=created_by,
    )


@pytest.fixture
def macro_clients():
    user_model = get_user_model()
    staff = user_model.objects.create_user(
        username="macro-staff",
        password="password123",
        is_staff=True,
    )
    owner = user_model.objects.create_user(username="macro-owner", password="password123")
    member = user_model.objects.create_user(username="macro-member", password="password123")
    outsider = user_model.objects.create_user(username="macro-outsider", password="password123")

    def build_client(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return {
        "staff": (build_client(staff), staff),
        "owner": (build_client(owner), owner),
        "member": (build_client(member), member),
        "outsider": (build_client(outsider), outsider),
    }


@pytest.mark.django_db
def test_macro_api_resolves_priority_and_enforces_permissions(macro_clients):
    staff_client, staff = macro_clients["staff"]
    owner_client, owner = macro_clients["owner"]
    member_client, member = macro_clients["member"]
    outsider_client, _ = macro_clients["outsider"]

    workspace = create_workspace(owner=owner)
    add_member(workspace, member)
    channel = create_channel(workspace=workspace, created_by=owner)

    global_response = staff_client.post(
        reverse("macro-list"),
        {
            "name": "\\RR",
            "definition": "\\mathbb{R}",
            "scope": "global",
        },
        format="json",
    )
    assert global_response.status_code == status.HTTP_201_CREATED

    workspace_response = owner_client.post(
        reverse("macro-list"),
        {
            "name": "\\RR",
            "definition": "\\mathbf{R}",
            "scope": "workspace",
            "workspace_id": workspace.id,
        },
        format="json",
    )
    assert workspace_response.status_code == status.HTTP_201_CREATED

    channel_response = owner_client.post(
        reverse("macro-list"),
        {
            "name": "\\RR",
            "definition": "\\operatorname{Room}",
            "scope": "channel",
            "channel_id": channel.id,
        },
        format="json",
    )
    assert channel_response.status_code == status.HTTP_201_CREATED

    extra_response = owner_client.post(
        reverse("macro-list"),
        {
            "name": "\\NN",
            "definition": "\\mathbb{N}",
            "scope": "workspace",
            "workspace_id": workspace.id,
        },
        format="json",
    )
    assert extra_response.status_code == status.HTTP_201_CREATED

    forbidden_global = member_client.post(
        reverse("macro-list"),
        {
            "name": "\\ZZ",
            "definition": "\\mathbb{Z}",
            "scope": "global",
        },
        format="json",
    )
    assert forbidden_global.status_code == status.HTTP_403_FORBIDDEN

    forbidden_workspace = outsider_client.post(
        reverse("macro-list"),
        {
            "name": "\\AA",
            "definition": "\\mathbb{A}",
            "scope": "workspace",
            "workspace_id": workspace.id,
        },
        format="json",
    )
    assert forbidden_workspace.status_code == status.HTTP_403_FORBIDDEN

    effective_response = member_client.get(
        reverse("macro-list"),
        {
            "channel_id": channel.id,
            "effective": "true",
        },
    )
    assert effective_response.status_code == status.HTTP_200_OK
    assert effective_response.json() == [
        {
            "id": extra_response.json()["id"],
            "name": "\\NN",
            "definition": "\\mathbb{N}",
            "scope": "workspace",
            "workspace_id": workspace.id,
            "channel_id": None,
            "updated_by": {
                "id": owner.id,
                "username": owner.username,
                "display_name": owner.username,
                "avatar_url": "",
                "discord_user_id": None,
            },
            "created_at": extra_response.json()["created_at"],
            "updated_at": extra_response.json()["updated_at"],
        },
        {
            "id": channel_response.json()["id"],
            "name": "\\RR",
            "definition": "\\operatorname{Room}",
            "scope": "channel",
            "workspace_id": None,
            "channel_id": channel.id,
            "updated_by": {
                "id": owner.id,
                "username": owner.username,
                "display_name": owner.username,
                "avatar_url": "",
                "discord_user_id": None,
            },
            "created_at": channel_response.json()["created_at"],
            "updated_at": channel_response.json()["updated_at"],
        },
    ]

    patch_response = owner_client.patch(
        reverse("macro-detail", args=[workspace_response.json()["id"]]),
        {"definition": "\\mathbb{WorkspaceR}"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert MacroDefinition.objects.get(pk=workspace_response.json()["id"]).definition == "\\mathbb{WorkspaceR}"

    denied_patch = member_client.patch(
        reverse("macro-detail", args=[workspace_response.json()["id"]]),
        {"definition": "\\mathbb{ShouldFail}"},
        format="json",
    )
    assert denied_patch.status_code == status.HTTP_403_FORBIDDEN
