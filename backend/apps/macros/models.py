from django.conf import settings
from django.db import models
from django.db.models import Q


class MacroDefinitionQuerySet(models.QuerySet):
    def accessible_to(self, user):
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(
            Q(scope=MacroDefinition.Scope.GLOBAL)
            | Q(scope=MacroDefinition.Scope.WORKSPACE, workspace__members=user)
            | Q(scope=MacroDefinition.Scope.CHANNEL, channel__workspace__members=user)
        ).distinct()


class MacroDefinition(models.Model):
    class Scope(models.TextChoices):
        GLOBAL = "global", "Global"
        WORKSPACE = "workspace", "Workspace"
        CHANNEL = "channel", "Channel"

    name = models.CharField(max_length=255)
    definition = models.TextField()
    scope = models.CharField(max_length=16, choices=Scope.choices)
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="macro_definitions",
    )
    channel = models.ForeignKey(
        "channels.Channel",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="macro_definitions",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="updated_macros",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MacroDefinitionQuerySet.as_manager()

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(scope="global", workspace__isnull=True, channel__isnull=True)
                    | Q(scope="workspace", workspace__isnull=False, channel__isnull=True)
                    | Q(scope="channel", workspace__isnull=True, channel__isnull=False)
                ),
                name="macro_scope_matches_target",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(scope="global", workspace__isnull=True, channel__isnull=True),
                name="unique_global_macro_name",
            ),
            models.UniqueConstraint(
                fields=["workspace", "name"],
                condition=Q(scope="workspace", channel__isnull=True),
                name="unique_workspace_macro_name",
            ),
            models.UniqueConstraint(
                fields=["channel", "name"],
                condition=Q(scope="channel", workspace__isnull=True),
                name="unique_channel_macro_name",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def can_view(self, user) -> bool:
        if user is None or not user.is_authenticated:
            return False
        if self.scope == self.Scope.GLOBAL:
            return True
        if self.scope == self.Scope.WORKSPACE:
            return self.workspace.has_member(user)
        return self.channel.workspace.has_member(user)

    def can_manage(self, user) -> bool:
        if user is None or not user.is_authenticated:
            return False
        if self.scope == self.Scope.GLOBAL:
            return user.is_staff
        if self.scope == self.Scope.WORKSPACE:
            return self.workspace.can_manage(user)
        return self.channel.workspace.can_manage(user)
