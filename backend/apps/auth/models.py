from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_profile")
    discord_user_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    discord_username = models.CharField(max_length=255, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)

    def resolved_display_name(self) -> str:
        return self.display_name or self.discord_username or self.user.username


class RefreshToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens")
    jti = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()
