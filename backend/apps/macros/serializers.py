from rest_framework import serializers

from apps.auth.services import serialize_user
from apps.channels.models import Channel
from apps.workspaces.models import Workspace

from .models import MacroDefinition


class MacroDefinitionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, validators=[])
    workspace_id = serializers.PrimaryKeyRelatedField(
        source="workspace",
        queryset=Workspace.objects.all(),
        allow_null=True,
        required=False,
    )
    channel_id = serializers.PrimaryKeyRelatedField(
        source="channel",
        queryset=Channel.objects.all(),
        allow_null=True,
        required=False,
    )
    updated_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MacroDefinition
        fields = [
            "id",
            "name",
            "definition",
            "scope",
            "workspace_id",
            "channel_id",
            "updated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_by", "created_at", "updated_at"]
        validators = []

    def get_updated_by(self, obj):
        return serialize_user(obj.updated_by)

    def validate(self, attrs):
        scope = attrs.get("scope", getattr(self.instance, "scope", None))
        workspace = attrs.get("workspace", getattr(self.instance, "workspace", None))
        channel = attrs.get("channel", getattr(self.instance, "channel", None))

        if self.instance is not None:
            if "scope" in attrs and attrs["scope"] != self.instance.scope:
                raise serializers.ValidationError({"scope": "Macro scope cannot be changed once created."})
            if "workspace" in attrs and attrs["workspace"] != self.instance.workspace:
                raise serializers.ValidationError(
                    {"workspace_id": "Macro workspace target cannot be changed once created."}
                )
            if "channel" in attrs and attrs["channel"] != self.instance.channel:
                raise serializers.ValidationError(
                    {"channel_id": "Macro channel target cannot be changed once created."}
                )

        if scope == MacroDefinition.Scope.GLOBAL:
            if workspace is not None or channel is not None:
                raise serializers.ValidationError(
                    {"scope": "Global macros cannot target a workspace or channel."}
                )
        elif scope == MacroDefinition.Scope.WORKSPACE:
            if workspace is None or channel is not None:
                raise serializers.ValidationError(
                    {"scope": "Workspace macros require workspace_id and cannot include channel_id."}
                )
        elif scope == MacroDefinition.Scope.CHANNEL:
            if channel is None or workspace is not None:
                raise serializers.ValidationError(
                    {"scope": "Channel macros require channel_id and cannot include workspace_id."}
                )

        return attrs
