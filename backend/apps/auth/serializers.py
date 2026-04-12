from rest_framework import serializers


class AuthenticatedUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True)
    discord_user_id = serializers.CharField(allow_null=True, allow_blank=True)

