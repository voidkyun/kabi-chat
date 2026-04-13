from rest_framework.permissions import BasePermission


class CanManageMacro(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return obj.can_manage(request.user)
