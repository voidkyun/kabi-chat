from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.channels.models import Channel

from .models import Message
from .serializers import MessageSerializer


class MessageListCreateView(APIView):
    def _channel(self, request):
        channel_id = request.query_params.get("channel_id")
        if channel_id:
            return Channel.objects.accessible_to(request.user).filter(pk=channel_id).first()
        return None

    def get(self, request):
        channel = self._channel(request)
        if channel is None:
            return Response(
                {"detail": "Query parameter channel_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages = Message.objects.accessible_to(request.user).filter(channel=channel).select_related(
            "author",
            "author__auth_profile",
        )
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MessageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
