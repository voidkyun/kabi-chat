from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.auth.services import serialize_user

from .models import Workspace, WorkspaceInvite, WorkspaceMembership


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        source="members",
        many=True,
        queryset=get_user_model().objects.all(),
        required=False,
    )

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "member_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "members", "created_at", "updated_at"]

    def get_owner(self, obj):
        return serialize_user(obj.owner)

    def get_members(self, obj):
        return [serialize_user(member) for member in obj.members.all().order_by("id")]

    def create(self, validated_data):
        members = list(validated_data.pop("members", []))
        request = self.context["request"]
        workspace = Workspace.objects.create(owner=request.user, **validated_data)
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=request.user,
            role=WorkspaceMembership.Role.OWNER,
        )
        self._sync_members(workspace, members)
        return workspace

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if members is not None:
            self._sync_members(instance, list(members))
        return instance

    def _sync_members(self, workspace: Workspace, members) -> None:
        requested_member_ids = {workspace.owner_id, *[member.pk for member in members]}
        existing_memberships = {
            membership.user_id: membership
            for membership in workspace.workspace_memberships.all()
        }

        workspace.workspace_memberships.exclude(user_id__in=requested_member_ids).delete()

        for user_id in requested_member_ids:
            membership = existing_memberships.get(user_id)
            role = (
                WorkspaceMembership.Role.OWNER
                if user_id == workspace.owner_id
                else WorkspaceMembership.Role.MEMBER
            )
            if membership is None:
                WorkspaceMembership.objects.create(
                    workspace=workspace,
                    user_id=user_id,
                    role=role,
                )
                continue
            if membership.role != role:
                membership.role = role
                membership.save(update_fields=["role"])


class WorkspaceInviteSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    accepted_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WorkspaceInvite
        fields = [
            "id",
            "created_by",
            "accepted_by",
            "expires_at",
            "accepted_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_created_by(self, obj):
        return serialize_user(obj.created_by)

    def get_accepted_by(self, obj):
        if obj.accepted_by is None:
            return None
        return serialize_user(obj.accepted_by)
