from django.conf import settings
from django.db import models


class MessageQuerySet(models.QuerySet):
    def accessible_to(self, user):
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(channel__workspace__members=user).distinct()


class Message(models.Model):
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.channel_id}:{self.author_id}"
