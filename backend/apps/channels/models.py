from django.conf import settings
from django.db import models


class ChannelQuerySet(models.QuerySet):
    def accessible_to(self, user):
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(workspace__members=user).distinct()


class Channel(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="channels",
    )
    name = models.CharField(max_length=255)
    topic = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_channels",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ChannelQuerySet.as_manager()

    class Meta:
        ordering = ["workspace_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name"],
                name="unique_channel_name_per_workspace",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def can_manage(self, user) -> bool:
        return self.workspace.can_manage(user)
