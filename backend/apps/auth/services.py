import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.utils import timezone

from .models import RefreshToken, UserProfile

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, code: str, detail: str, status_code: int):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


def serialize_user(user) -> dict[str, object]:
    profile = getattr(user, "auth_profile", None)
    display_name = user.username
    avatar_url = ""
    discord_user_id = None
    if profile is not None:
        display_name = profile.resolved_display_name()
        avatar_url = profile.avatar_url
        discord_user_id = profile.discord_user_id

    return {
        "id": user.id,
        "username": user.username,
        "display_name": display_name,
        "avatar_url": avatar_url,
        "discord_user_id": discord_user_id,
    }


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class DiscordOAuthService:
    authorization_endpoint = "https://discord.com/oauth2/authorize"
    token_endpoint = "https://discord.com/api/oauth2/token"
    user_endpoint = "https://discord.com/api/users/@me"
    default_user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )

    def _build_headers(self, headers: dict[str, str]) -> dict[str, str]:
        merged_headers = {
            "User-Agent": os.getenv("DISCORD_HTTP_USER_AGENT", self.default_user_agent),
        }
        merged_headers.update(headers)
        return merged_headers

    def build_authorization_url(self, state: str) -> str:
        client_id = os.getenv("DISCORD_CLIENT_ID", "")
        redirect_uri = os.getenv("DISCORD_REDIRECT_URI", "")
        if not client_id or client_id == "replace-me" or not redirect_uri:
            raise AuthError(
                "discord_oauth_not_configured",
                "Discord OAuth2 settings are not configured.",
                500,
            )

        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "identify",
                "state": state,
            }
        )
        return f"{self.authorization_endpoint}?{query}"

    def exchange_code(self, code: str) -> dict[str, object]:
        request = Request(
            self.token_endpoint,
            data=urlencode(
                {
                    "client_id": os.getenv("DISCORD_CLIENT_ID", ""),
                    "client_secret": os.getenv("DISCORD_CLIENT_SECRET", ""),
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": os.getenv("DISCORD_REDIRECT_URI", ""),
                }
            ).encode(),
            headers=self._build_headers(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            ),
            method="POST",
        )
        payload = self._request_json(request, invalid_code_status=400)
        access_token = payload.get("access_token")
        if not access_token:
            raise AuthError(
                "invalid_authorization_code",
                "Discord did not return an access token.",
                400,
            )
        return payload

    def fetch_user(self, access_token: str) -> dict[str, object]:
        request = Request(
            self.user_endpoint,
            headers=self._build_headers(
                {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }
            ),
            method="GET",
        )
        payload = self._request_json(request, invalid_code_status=502)
        user_id = payload.get("id")
        username = payload.get("username")
        if not user_id or not username:
            raise AuthError(
                "discord_user_fetch_failed",
                "Discord user information was incomplete.",
                502,
            )

        avatar_hash = payload.get("avatar")
        avatar_url = ""
        if avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

        return {
            "discord_user_id": str(user_id),
            "discord_username": username,
            "display_name": payload.get("global_name") or username,
            "avatar_url": avatar_url,
        }

    def _request_json(self, request: Request, invalid_code_status: int) -> dict[str, object]:
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            detail = "Discord rejected the request."
            raw_body = ""
            try:
                raw_body = exc.read().decode()
                payload = json.loads(raw_body)
                error_code = payload.get("error")
                error_description = payload.get("error_description")
                if error_description:
                    detail = error_description
                elif error_code == "invalid_grant":
                    detail = (
                        "Discord rejected the authorization code. "
                        "It may be expired, already used, or the redirect URI may not match."
                    )
                elif payload.get("message"):
                    detail = str(payload["message"])
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            logger.warning(
                "Discord API request failed: url=%s status=%s body=%r",
                request.full_url,
                exc.code,
                raw_body[:500],
            )
            status_code = invalid_code_status if exc.code < 500 else 502
            code = "invalid_authorization_code" if status_code == 400 else "discord_unavailable"
            raise AuthError(code, detail, status_code) from exc
        except URLError as exc:
            raise AuthError("discord_unavailable", "Discord OAuth2 is unavailable.", 502) from exc


class JWTService:
    algorithm = "HS256"

    def issue_access_token(self, user, *, expires_at: datetime | None = None) -> str:
        if expires_at is None:
            expires_at = timezone.now() + timedelta(seconds=settings.AUTH_ACCESS_TOKEN_LIFETIME_SECONDS)
        payload = {
            "sub": str(user.pk),
            "type": "access",
            "iat": self._to_timestamp(timezone.now()),
            "exp": self._to_timestamp(expires_at),
        }
        return self._encode(payload)

    def issue_refresh_token(
        self,
        user,
        *,
        jti: str,
        expires_at: datetime | None = None,
    ) -> str:
        if expires_at is None:
            expires_at = timezone.now() + timedelta(days=settings.AUTH_REFRESH_TOKEN_LIFETIME_DAYS)
        payload = {
            "sub": str(user.pk),
            "type": "refresh",
            "jti": jti,
            "iat": self._to_timestamp(timezone.now()),
            "exp": self._to_timestamp(expires_at),
        }
        return self._encode(payload)

    def decode_access_token(self, token: str) -> dict[str, object]:
        claims = self._decode(token)
        self._validate_claims(claims, expected_type="access", expired_code="access_token_expired")
        return claims

    def decode_refresh_token(self, token: str) -> dict[str, object]:
        claims = self._decode(token)
        self._validate_claims(claims, expected_type="refresh", expired_code="invalid_refresh_token")
        return claims

    def _validate_claims(self, claims: dict[str, object], *, expected_type: str, expired_code: str) -> None:
        token_type = claims.get("type")
        if token_type != expected_type:
            raise AuthError("invalid_token_type", f"Expected a {expected_type} token.", 401)

        exp = claims.get("exp")
        if not isinstance(exp, int):
            raise AuthError("invalid_token", "Token expiration is missing.", 401)
        if exp <= self._to_timestamp(timezone.now()):
            detail = "Access token has expired." if expected_type == "access" else "Refresh token is invalid."
            raise AuthError(expired_code, detail, 401)

    def _encode(self, payload: dict[str, object]) -> str:
        header = {"alg": self.algorithm, "typ": "JWT"}
        signing_input = ".".join(
            [
                self._b64encode(json.dumps(header, separators=(",", ":")).encode()),
                self._b64encode(json.dumps(payload, separators=(",", ":")).encode()),
            ]
        )
        signature = hmac.new(
            settings.JWT_SIGNING_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        return f"{signing_input}.{self._b64encode(signature)}"

    def _decode(self, token: str) -> dict[str, object]:
        try:
            header_segment, payload_segment, signature_segment = token.split(".")
        except ValueError as exc:
            raise AuthError("invalid_token", "Token format is invalid.", 401) from exc

        signing_input = f"{header_segment}.{payload_segment}"
        expected_signature = hmac.new(
            settings.JWT_SIGNING_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        received_signature = self._b64decode(signature_segment)
        if not hmac.compare_digest(expected_signature, received_signature):
            raise AuthError("invalid_token", "Token signature is invalid.", 401)

        try:
            header = json.loads(self._b64decode(header_segment).decode())
            payload = json.loads(self._b64decode(payload_segment).decode())
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise AuthError("invalid_token", "Token payload is invalid.", 401) from exc

        if header.get("alg") != self.algorithm:
            raise AuthError("invalid_token", "Token algorithm is invalid.", 401)

        return payload

    def _b64encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _b64decode(self, data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(f"{data}{padding}")

    def _to_timestamp(self, value: datetime) -> int:
        return int(value.astimezone(UTC).timestamp())


class RefreshTokenService:
    def __init__(self):
        self.jwt_service = JWTService()

    def issue_token_pair(self, user) -> TokenPair:
        refresh_token, _ = self._create_refresh_token(user)
        return TokenPair(
            access_token=self.jwt_service.issue_access_token(user),
            refresh_token=refresh_token,
            expires_in=settings.AUTH_ACCESS_TOKEN_LIFETIME_SECONDS,
        )

    @transaction.atomic
    def rotate_refresh_token(self, raw_refresh_token: str) -> TokenPair:
        claims = self.jwt_service.decode_refresh_token(raw_refresh_token)
        record = self._get_active_record(claims)
        record.revoked_at = timezone.now()
        record.save(update_fields=["revoked_at", "updated_at"])

        refresh_token, _ = self._create_refresh_token(record.user)
        return TokenPair(
            access_token=self.jwt_service.issue_access_token(record.user),
            refresh_token=refresh_token,
            expires_in=settings.AUTH_ACCESS_TOKEN_LIFETIME_SECONDS,
        )

    @transaction.atomic
    def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        claims = self.jwt_service.decode_refresh_token(raw_refresh_token)
        record = self._get_active_record(claims)
        record.revoked_at = timezone.now()
        record.save(update_fields=["revoked_at", "updated_at"])

    def upsert_discord_user(self, discord_user: dict[str, str]):
        user_model = get_user_model()
        discord_user_id = discord_user["discord_user_id"]
        profile_defaults = {
            "discord_username": discord_user["discord_username"],
            "display_name": discord_user["display_name"],
            "avatar_url": discord_user["avatar_url"],
        }
        profile = UserProfile.objects.select_related("user").filter(
            discord_user_id=discord_user_id,
        ).first()
        if profile is not None:
            for field, value in profile_defaults.items():
                setattr(profile, field, value)
            profile.save(update_fields=list(profile_defaults.keys()))
            return profile.user

        user = user_model.objects.create_user(username=f"discord_{discord_user_id}")
        UserProfile.objects.create(
            user=user,
            discord_user_id=discord_user_id,
            **profile_defaults,
        )
        return user

    def generate_oauth_state(self) -> str:
        return secrets.token_urlsafe(32)

    def dump_oauth_state(self, state: str) -> str:
        return signing.dumps(state)

    def load_oauth_state(self, signed_state: str) -> str:
        try:
            return signing.loads(signed_state, max_age=settings.AUTH_OAUTH_STATE_MAX_AGE_SECONDS)
        except signing.BadSignature as exc:
            raise AuthError("invalid_state", "OAuth state is invalid or expired.", 400) from exc

    def _create_refresh_token(self, user) -> tuple[str, RefreshToken]:
        jti = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=settings.AUTH_REFRESH_TOKEN_LIFETIME_DAYS)
        refresh_token = self.jwt_service.issue_refresh_token(user, jti=jti, expires_at=expires_at)
        record = RefreshToken.objects.create(user=user, jti=jti, expires_at=expires_at)
        return refresh_token, record

    def _get_active_record(self, claims: dict[str, object]) -> RefreshToken:
        jti = claims.get("jti")
        user_id = claims.get("sub")
        if not isinstance(jti, str) or not isinstance(user_id, str):
            raise AuthError("invalid_refresh_token", "Refresh token payload is invalid.", 401)

        try:
            record = RefreshToken.objects.select_related("user").get(jti=jti, user_id=int(user_id))
        except (RefreshToken.DoesNotExist, ValueError) as exc:
            raise AuthError("invalid_refresh_token", "Refresh token is invalid.", 401) from exc

        if record.revoked_at is not None or record.expires_at <= timezone.now():
            raise AuthError("invalid_refresh_token", "Refresh token is invalid.", 401)
        return record
