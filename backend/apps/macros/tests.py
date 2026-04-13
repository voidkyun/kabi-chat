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

    effective_with_workspace_response = member_client.get(
        reverse("macro-list"),
        {
            "workspace_id": workspace.id,
            "channel_id": channel.id,
            "effective": "true",
        },
    )
    assert effective_with_workspace_response.status_code == status.HTTP_200_OK
    assert effective_with_workspace_response.json() == effective_response.json()

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


@pytest.mark.django_db
def test_macro_create_rejects_duplicate_name_in_same_scope(macro_clients):
    staff_client, _ = macro_clients["staff"]

    first_response = staff_client.post(
        reverse("macro-list"),
        {
            "name": "\\RR",
            "definition": "\\mathbb{R}",
            "scope": "global",
        },
        format="json",
    )
    assert first_response.status_code == status.HTTP_201_CREATED

    duplicate_response = staff_client.post(
        reverse("macro-list"),
        {
            "name": "\\RR",
            "definition": "\\mathbf{R}",
            "scope": "global",
        },
        format="json",
    )

    assert duplicate_response.status_code == status.HTTP_400_BAD_REQUEST
    assert duplicate_response.json() == {
        "name": ["A macro with this name already exists for this scope."]
    }


@pytest.mark.django_db
def test_macro_list_rejects_non_integer_scope_filters(macro_clients):
    owner_client, _ = macro_clients["owner"]

    workspace_response = owner_client.get(reverse("macro-list"), {"workspace_id": "abc"})
    channel_response = owner_client.get(reverse("macro-list"), {"channel_id": "abc"})

    assert workspace_response.status_code == status.HTTP_400_BAD_REQUEST
    assert workspace_response.json() == {"workspace_id": "Must be an integer."}
    assert channel_response.status_code == status.HTTP_400_BAD_REQUEST
    assert channel_response.json() == {"channel_id": "Must be an integer."}


@pytest.mark.django_db
def test_macro_list_rejects_non_positive_scope_filters(macro_clients):
    owner_client, _ = macro_clients["owner"]

    workspace_response = owner_client.get(reverse("macro-list"), {"workspace_id": 0})
    channel_response = owner_client.get(reverse("macro-list"), {"channel_id": 0})

    assert workspace_response.status_code == status.HTTP_400_BAD_REQUEST
    assert workspace_response.json() == {"workspace_id": "Must be a positive integer."}
    assert channel_response.status_code == status.HTTP_400_BAD_REQUEST
    assert channel_response.json() == {"channel_id": "Must be a positive integer."}


@pytest.mark.django_db
def test_macro_effective_rejects_mismatched_workspace_and_channel(macro_clients):
    owner_client, owner = macro_clients["owner"]

    workspace = create_workspace(owner=owner)
    other_workspace = create_workspace(owner=owner)
    other_channel = create_channel(workspace=other_workspace, created_by=owner)

    response = owner_client.get(
        reverse("macro-list"),
        {
            "effective": "true",
            "workspace_id": workspace.id,
            "channel_id": other_channel.id,
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "workspace_id and channel_id must belong to the same workspace."
    }


@pytest.mark.django_db
def test_staff_cannot_create_scoped_macro_without_workspace_ownership(macro_clients):
    staff_client, staff = macro_clients["staff"]
    owner_client, owner = macro_clients["owner"]

    workspace = create_workspace(owner=owner)
    add_member(workspace, staff)
    channel = create_channel(workspace=workspace, created_by=owner)

    workspace_response = staff_client.post(
        reverse("macro-list"),
        {
            "name": "\\Scoped",
            "definition": "\\text{workspace}",
            "scope": "workspace",
            "workspace_id": workspace.id,
        },
        format="json",
    )
    channel_response = staff_client.post(
        reverse("macro-list"),
        {
            "name": "\\ScopedChannel",
            "definition": "\\text{channel}",
            "scope": "channel",
            "channel_id": channel.id,
        },
        format="json",
    )

    assert workspace_response.status_code == status.HTTP_403_FORBIDDEN
    assert channel_response.status_code == status.HTTP_403_FORBIDDEN

    owner_response = owner_client.post(
        reverse("macro-list"),
        {
            "name": "\\OwnerScoped",
            "definition": "\\text{owner}",
            "scope": "workspace",
            "workspace_id": workspace.id,
        },
        format="json",
    )
    assert owner_response.status_code == status.HTTP_201_CREATED
