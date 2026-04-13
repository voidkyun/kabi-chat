from rest_framework import serializers

from apps.auth.services import serialize_user
from apps.channels.models import Channel

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    channel_id = serializers.PrimaryKeyRelatedField(
        source="channel",
        queryset=Channel.objects.all(),
    )
    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "channel_id",
            "body",
            "author",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_author(self, obj):
        return serialize_user(obj.author)

    def validate_channel_id(self, channel):
        request = self.context["request"]
        if not channel.workspace.has_member(request.user):
            raise serializers.ValidationError("You do not have access to this channel.")
        return channel
