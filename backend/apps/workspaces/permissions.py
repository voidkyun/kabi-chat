from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsWorkspaceMemberOrManager(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return obj.has_member(request.user) or obj.can_manage(request.user)
        return obj.can_manage(request.user)
