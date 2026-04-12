from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .services import AuthError, JWTService


class JWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def __init__(self):
        self.jwt_service = JWTService()

    def authenticate(self, request):
        auth_header = get_authorization_header(request).split()
        if not auth_header:
            return None
        if auth_header[0].lower() != self.keyword:
            return None
        if len(auth_header) != 2:
            raise AuthenticationFailed(
                {"error": "invalid_authorization_header", "detail": "Authorization header must be Bearer <token>."}
            )

        token = auth_header[1].decode()
        try:
            claims = self.jwt_service.decode_access_token(token)
        except AuthError as exc:
            raise AuthenticationFailed({"error": exc.code, "detail": exc.detail}) from exc

        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=int(claims["sub"]))
        except (user_model.DoesNotExist, KeyError, ValueError) as exc:
            raise AuthenticationFailed(
                {"error": "invalid_token", "detail": "Access token user does not exist."}
            ) from exc

        if not user.is_active:
            raise AuthenticationFailed({"error": "inactive_user", "detail": "User account is inactive."})
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
