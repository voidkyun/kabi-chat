from django.conf import settings
from django.db import models


class WorkspaceQuerySet(models.QuerySet):
    def accessible_to(self, user):
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(members=user).distinct()


class Workspace(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_workspaces",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="WorkspaceMembership",
        related_name="workspaces",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkspaceQuerySet.as_manager()

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name

    def has_member(self, user) -> bool:
        return bool(user and user.is_authenticated and self.members.filter(pk=user.pk).exists())

    def can_manage(self, user) -> bool:
        return bool(user and user.is_authenticated and self.owner_id == user.pk)


class WorkspaceMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MEMBER = "member", "Member"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="unique_workspace_membership",
            )
        ]
        ordering = ["workspace_id", "user_id"]

    def __str__(self) -> str:
        return f"{self.workspace_id}:{self.user_id}:{self.role}"
