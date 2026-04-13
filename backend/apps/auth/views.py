from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AuthenticatedUserSerializer
from .services import AuthError, DiscordOAuthService, RefreshTokenService, serialize_user


def error_response(error: AuthError) -> Response:
    return Response({"error": error.code, "detail": error.detail}, status=error.status_code)


def build_frontend_callback_url(params: dict[str, str], *, use_fragment: bool) -> str | None:
    callback_url = settings.AUTH_FRONTEND_CALLBACK_URL.strip()
    if not callback_url:
        return None

    split_result = urlsplit(callback_url)
    query_params = dict(parse_qsl(split_result.query, keep_blank_values=True))
    fragment_params = dict(parse_qsl(split_result.fragment, keep_blank_values=True))
    if use_fragment:
        fragment_params.update(params)
    else:
        query_params.update(params)

    return urlunsplit(
        (
            split_result.scheme,
            split_result.netloc,
            split_result.path,
            urlencode(query_params),
            urlencode(fragment_params),
        )
    )


def callback_error_response(error: AuthError) -> Response | HttpResponseRedirect:
    redirect_url = build_frontend_callback_url(
        {"error": error.code, "detail": error.detail},
        use_fragment=False,
    )
    if redirect_url:
        return HttpResponseRedirect(redirect_url)
    return error_response(error)


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        settings.AUTH_REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        max_age=settings.AUTH_REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )


def delete_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.AUTH_REFRESH_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def set_oauth_state_cookie(response: Response, signed_state: str) -> None:
    response.set_cookie(
        settings.AUTH_OAUTH_STATE_COOKIE_NAME,
        signed_state,
        max_age=settings.AUTH_OAUTH_STATE_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )


def delete_oauth_state_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.AUTH_OAUTH_STATE_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


class DiscordLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        token_service = RefreshTokenService()
        oauth_service = DiscordOAuthService()
        state = token_service.generate_oauth_state()
        try:
            authorization_url = oauth_service.build_authorization_url(state)
        except AuthError as error:
            return error_response(error)

        response = Response(
            {
                "provider": "discord",
                "authorization_url": authorization_url,
                "state": state,
            }
        )
        set_oauth_state_cookie(response, token_service.dump_oauth_state(state))
        return response


class DiscordCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        if request.query_params.get("error"):
            return callback_error_response(
                AuthError("discord_access_denied", "Discord authorization was denied.", 400)
            )

        raw_state_cookie = request.COOKIES.get(settings.AUTH_OAUTH_STATE_COOKIE_NAME)
        if not raw_state_cookie:
            return callback_error_response(AuthError("invalid_state", "OAuth state is missing.", 400))

        token_service = RefreshTokenService()
        try:
            expected_state = token_service.load_oauth_state(raw_state_cookie)
        except AuthError as error:
            return callback_error_response(error)

        received_state = request.query_params.get("state")
        if not received_state or received_state != expected_state:
            return callback_error_response(AuthError("invalid_state", "OAuth state did not match.", 400))

        code = request.query_params.get("code")
        if not code:
            return callback_error_response(
                AuthError("invalid_authorization_code", "Authorization code is missing.", 400)
            )

        oauth_service = DiscordOAuthService()
        try:
            discord_token = oauth_service.exchange_code(code)
            discord_user = oauth_service.fetch_user(discord_token["access_token"])
            user = token_service.upsert_discord_user(discord_user)
            token_pair = token_service.issue_token_pair(user)
        except AuthError as error:
            response = callback_error_response(error)
            delete_oauth_state_cookie(response)
            return response

        redirect_url = build_frontend_callback_url(
            {
                "access_token": token_pair.access_token,
                "token_type": "Bearer",
                "expires_in": str(token_pair.expires_in),
            },
            use_fragment=True,
        )
        if redirect_url:
            response = HttpResponseRedirect(redirect_url)
        else:
            response = Response(
                {
                    "access_token": token_pair.access_token,
                    "token_type": "Bearer",
                    "expires_in": token_pair.expires_in,
                    "user": AuthenticatedUserSerializer(serialize_user(user)).data,
                }
            )
        set_refresh_token_cookie(response, token_pair.refresh_token)
        delete_oauth_state_cookie(response)
        return response


class CurrentUserView(APIView):
    def get(self, request):
        user_data = serialize_user(request.user)
        return Response({"authenticated": True, **AuthenticatedUserSerializer(user_data).data})


class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
            return error_response(
                AuthError("missing_refresh_token", "Refresh token cookie is missing.", 401)
            )

        token_service = RefreshTokenService()
        try:
            token_pair = token_service.rotate_refresh_token(refresh_token)
        except AuthError as error:
            response = error_response(error)
            delete_refresh_token_cookie(response)
            return response

        response = Response(
            {
                "access_token": token_pair.access_token,
                "token_type": "Bearer",
                "expires_in": token_pair.expires_in,
            }
        )
        set_refresh_token_cookie(response, token_pair.refresh_token)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
            return error_response(
                AuthError("missing_refresh_token", "Refresh token cookie is missing.", 401)
            )

        token_service = RefreshTokenService()
        try:
            token_service.revoke_refresh_token(refresh_token)
        except AuthError as error:
            response = error_response(error)
            delete_refresh_token_cookie(response)
            return response

        response = Response({"detail": "Logged out."})
        delete_refresh_token_cookie(response)
        return response
