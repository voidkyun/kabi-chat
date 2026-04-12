from rest_framework import serializers

from apps.auth.services import serialize_user
from apps.workspaces.models import Workspace

from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
    workspace_id = serializers.PrimaryKeyRelatedField(
        source="workspace",
        queryset=Workspace.objects.all(),
    )
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Channel
        fields = [
            "id",
            "workspace_id",
            "name",
            "topic",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_created_by(self, obj):
        return serialize_user(obj.created_by)

    def validate_workspace_id(self, workspace):
        request = self.context["request"]
        if not workspace.has_member(request.user):
            raise serializers.ValidationError("You do not have access to this workspace.")
        return workspace

    def validate(self, attrs):
        workspace = attrs.get("workspace")
        if self.instance is not None and workspace is not None and workspace != self.instance.workspace:
            raise serializers.ValidationError(
                {"workspace_id": "Channel workspace cannot be changed once created."}
            )
        return attrs
