# -*- coding: utf-8 -*-

from .guards import Guard
from .exceptions import ObjectPermissionException
#import django.contrib.auth.backends.ModelBackend

class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None
    
    def get_guard(self, obj):
        guard = getattr(obj, 'get_guard', lambda: None)()
        if not isinstance(guard, Guard):
            raise ObjectPermissionException('obj.get_guard() must return a Guard instance.')
        return guard
    
    def has_perm(self, user, perm, obj=None):
        # Only check row (object) level permissions
        if obj is None:
            return False
        
        # Inactive users never have permissions
        if not user.is_active:
            return False
        
        # Anonymous users
        if user.is_anonymous():
            return False
        # TODO: permissions for anonymous users
        guard = self.get_guard(obj)
        return guard.full_check(user=user, perm=perm, obj=obj) if guard else False
    
    def has_module_perms(self, user, app_label):
        raise ObjectPermissionException('Not implemented.')
    
    def get_all_permissions(self, user, obj):
        if not hasattr(user, '_perm_cache_obj'):
            guard = self.get_guard(obj)
            user._perm_cache_obj = guard.get_all_permissions(user, obj) if guard else set()
        return user._perm_cache_obj
    
    """
    def get_group_permissions(self, user, obj):
        if not hasattr(user, '_group_perm_cache_obj'):
            guard = self.get_guard(obj)
            user._group_perm_cache_obj = guard.get_group_permissions(user, obj) if guard else set()
        return user._group_perm_cache_obj
    """ 