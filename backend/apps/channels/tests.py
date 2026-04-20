import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.workspaces.models import Workspace, WorkspaceMembership

from .models import Channel


def create_workspace(*, owner, name="Workspace"):
    workspace = Workspace.objects.create(name=name, owner=owner)
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
def setup_clients():
    user_model = get_user_model()
    owner = user_model.objects.create_user(username="channel-owner", password="password123")
    member = user_model.objects.create_user(username="channel-member", password="password123")
    outsider = user_model.objects.create_user(username="channel-outsider", password="password123")

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
def test_channel_api_requires_workspace_access_and_owner_for_updates(setup_clients):
    owner_client, owner = setup_clients["owner"]
    member_client, member = setup_clients["member"]
    outsider_client, _ = setup_clients["outsider"]

    workspace = create_workspace(owner=owner, name="Geometry")
    add_member(workspace, member)

    create_response = owner_client.post(
        reverse("channel-list"),
        {
            "workspace_id": workspace.id,
            "name": "proofs",
            "topic": "Discuss proofs",
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    channel_id = create_response.json()["id"]
    assert create_response.json()["created_by"]["id"] == owner.id

    list_response = owner_client.get(reverse("channel-list"), {"workspace_id": workspace.id})
    assert list_response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in list_response.json()] == [channel_id]

    member_create_response = member_client.post(
        reverse("channel-list"),
        {
            "workspace_id": workspace.id,
            "name": "member-created",
            "topic": "Should be rejected",
        },
        format="json",
    )
    assert member_create_response.status_code == status.HTTP_400_BAD_REQUEST
    assert member_create_response.json() == {
        "workspace_id": [
            "You do not have permission to create channels in this workspace."
        ]
    }

    outsider_response = outsider_client.post(
        reverse("channel-list"),
        {
            "workspace_id": workspace.id,
            "name": "forbidden",
        },
        format="json",
    )
    assert outsider_response.status_code == status.HTTP_400_BAD_REQUEST

    member_patch = member_client.patch(
        reverse("channel-detail", args=[channel_id]),
        {"topic": "Updated by member"},
        format="json",
    )
    assert member_patch.status_code == status.HTTP_403_FORBIDDEN

    owner_patch = owner_client.patch(
        reverse("channel-detail", args=[channel_id]),
        {"topic": "Updated by owner"},
        format="json",
    )
    assert owner_patch.status_code == status.HTTP_200_OK
    assert owner_patch.json()["topic"] == "Updated by owner"

    assert Channel.objects.get(pk=channel_id).topic == "Updated by owner"

    member_delete = member_client.delete(reverse("channel-detail", args=[channel_id]))
    assert member_delete.status_code == status.HTTP_403_FORBIDDEN

    owner_delete = owner_client.delete(reverse("channel-detail", args=[channel_id]))
    assert owner_delete.status_code == status.HTTP_204_NO_CONTENT
    assert Channel.objects.filter(pk=channel_id).count() == 0


@pytest.mark.django_db
def test_channel_list_rejects_non_integer_workspace_id(setup_clients):
    owner_client, _ = setup_clients["owner"]

    response = owner_client.get(reverse("channel-list"), {"workspace_id": "abc"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"workspace_id": "Must be an integer."}


@pytest.mark.django_db
def test_channel_list_rejects_non_positive_workspace_id(setup_clients):
    owner_client, _ = setup_clients["owner"]

    response = owner_client.get(reverse("channel-list"), {"workspace_id": 0})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"workspace_id": "Must be a positive integer."}
