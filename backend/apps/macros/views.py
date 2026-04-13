from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.channels.models import Channel
from apps.workspaces.models import Workspace

from .models import MacroDefinition
from .permissions import CanManageMacro
from .serializers import MacroDefinitionSerializer
from .services import resolve_effective_macros


class MacroListCreateView(APIView):
    def _parse_effective(self, value: str | None) -> bool:
        return str(value).lower() in {"1", "true", "yes", "on"}

    def _parse_optional_int_query(self, request, param_name: str):
        value = request.query_params.get(param_name)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError({param_name: "Must be an integer."}) from exc

    def _workspace(self, request):
        workspace_id = self._parse_optional_int_query(request, "workspace_id")
        if not workspace_id:
            return None
        return Workspace.objects.accessible_to(request.user).filter(pk=workspace_id).first()

    def _channel(self, request):
        channel_id = self._parse_optional_int_query(request, "channel_id")
        if not channel_id:
            return None
        return Channel.objects.accessible_to(request.user).filter(pk=channel_id).first()

    def get(self, request):
        if self._parse_effective(request.query_params.get("effective")):
            channel = self._channel(request)
            workspace = self._workspace(request)
            if channel is None and workspace is None:
                raise ValidationError(
                    {"detail": "effective=true requires workspace_id or channel_id."}
                )
            macros = resolve_effective_macros(workspace=workspace, channel=channel)
            serializer = MacroDefinitionSerializer(macros, many=True)
            return Response(serializer.data)

        queryset = MacroDefinition.objects.accessible_to(request.user).select_related(
            "workspace",
            "channel",
            "channel__workspace",
            "updated_by",
            "updated_by__auth_profile",
        )
        scope = request.query_params.get("scope")
        if scope:
            queryset = queryset.filter(scope=scope)

        workspace = self._workspace(request)
        channel = self._channel(request)
        if request.query_params.get("workspace_id") and workspace is None:
            queryset = queryset.none()
        elif workspace is not None:
            queryset = queryset.filter(workspace=workspace)

        if request.query_params.get("channel_id") and channel is None:
            queryset = queryset.none()
        elif channel is not None:
            queryset = queryset.filter(channel=channel)

        serializer = MacroDefinitionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MacroDefinitionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self._enforce_create_permission(request, serializer.validated_data)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _enforce_create_permission(self, request, validated_data) -> None:
        scope = validated_data["scope"]
        workspace = validated_data.get("workspace")
        channel = validated_data.get("channel")

        if scope == MacroDefinition.Scope.GLOBAL:
            if not request.user.is_staff:
                raise PermissionDenied("Only staff users can manage global macros.")
            return

        target_workspace = workspace if workspace is not None else channel.workspace
        if not target_workspace.can_manage(request.user):
            raise PermissionDenied("Only workspace managers can manage scoped macros.")


class MacroDetailView(generics.UpdateAPIView):
    serializer_class = MacroDefinitionSerializer
    permission_classes = [CanManageMacro]

    def get_queryset(self):
        return MacroDefinition.objects.accessible_to(self.request.user).select_related(
            "workspace",
            "channel",
            "channel__workspace",
            "updated_by",
            "updated_by__auth_profile",
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
