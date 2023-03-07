from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    '''Права доступа для администратора'''
    def has_permission(self, request, view):
        return request.user.is_admin


class IsAdminOrReadOnly(permissions.BasePermission):
    '''Права доступа для администратора, либо только на чтение'''
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and (
                request.user.is_admin or request.user.is_superuser)))


class IsAdminOrModeratorIsAuthorOrReadOnly(permissions.BasePermission):
    '''Права доступа для администратора или модератора,
    либо только на чтение'''
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                obj.author == request.user
                or request.user.is_moderator
                or request.user.is_admin
            )
        )
