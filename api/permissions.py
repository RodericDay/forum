from rest_framework import permissions


class ReadIfAuthEditIfAdminOrOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return obj.author == request.user.username or request.user.is_superuser
