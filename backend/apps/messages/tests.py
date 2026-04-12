import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.channels.models import Channel
from apps.workspaces.models import Workspace, WorkspaceMembership


def create_workspace(*, owner):
    workspace = Workspace.objects.create(name="Messaging", owner=owner)
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


def create_channel(*, workspace, created_by, name="general"):
    return Channel.objects.create(
        workspace=workspace,
        name=name,
        topic="",
        created_by=created_by,
    )


@pytest.fixture
def client_setup():
    user_model = get_user_model()
    owner = user_model.objects.create_user(username="message-owner", password="password123")
    member = user_model.objects.create_user(username="message-member", password="password123")
    outsider = user_model.objects.create_user(username="message-outsider", password="password123")

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
def test_message_api_lists_and_creates_messages_with_channel_scope(client_setup):
    owner_client, owner = client_setup["owner"]
    member_client, member = client_setup["member"]
    outsider_client, _ = client_setup["outsider"]

    workspace = create_workspace(owner=owner)
    add_member(workspace, member)
    channel = create_channel(workspace=workspace, created_by=owner)

    missing_channel_response = member_client.get(reverse("message-list"))
    assert missing_channel_response.status_code == status.HTTP_400_BAD_REQUEST

    create_response = member_client.post(
        reverse("message-list"),
        {
            "channel_id": channel.id,
            "body": "Hello from member",
        },
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.json()["author"]["id"] == member.id

    list_response = owner_client.get(reverse("message-list"), {"channel_id": channel.id})
    assert list_response.status_code == status.HTTP_200_OK
    assert [item["body"] for item in list_response.json()] == ["Hello from member"]

    outsider_response = outsider_client.post(
        reverse("message-list"),
        {
            "channel_id": channel.id,
            "body": "Should fail",
        },
        format="json",
    )
    assert outsider_response.status_code == status.HTTP_400_BAD_REQUEST
