from collections import defaultdict
from django.db import models
from django.template.defaultfilters import slugify
from .exceptions import GuardException


class Guard(object):
    perms = None
    def __init__(self, perms=None, default_for_perms=False):
        """
        perms is required if you use get_all_permissions() or get_group_permissions()
        perms can be a:
            * dictionary, i.e. {'app_lable.permission_name': True} 
            * list, i.e. ['app_lable.permission_name'] or ['just_the_permission_name']
        default_for_perms is the boolean returned by the full_check() 
            in case there was no decision on a specific permission. 
        """
        self.perms = perms
        self.default_for_perms = default_for_perms

    def get_all_perms(self):
        """
        Returns all the permissions handled by this Guard 
        """
        if self.perms is None:
            raise GuardException("You must pass the 'perms' argument to the Guard subclass")
        
        if not self.perms:
            return set()
         
        if isinstance(self.perms, dict):
            return set(self.perms.keys())
        
        if isinstance(self.perms, list):
            return set(self.perms)

    def get_default_for_perm(self, perm):
        if self.perms and isinstance(self.perms, dict):
            return self.perms[perm]
        else:
            return self.default_for_perms
    
    def unpack_perm(self, perm):
        if "." in perm:
            app_label, perm_name = str(perm).split(".", 2)
        else:
            app_label = ''
            perm_name = str(perm)
        
        # TODO: test app_label format as well
        if perm_name != slugify(perm_name).replace('-', '_'):
            raise GuardException("'perm' must only contain alphanumeric characters")

        return app_label, str(perm_name)
    
    def get_check_methods(self, perm):
        app_label, perm_name = self.unpack_perm(perm)
        return ('check_%s'%perm_name, 'check')
    
    def full_check(self, user, perm, obj, from_user=True, from_groups=True):
        """
        dispatcher
        """
        # TODO: support app_label, obj's Model belongs to an app, look into the "django_content_type" table
        
        if not (from_user or from_groups):
            return None
        
        is_authorized = None
        app_label, perm_name = self.unpack_perm(perm)
        
        for perm_method in self.get_check_methods(perm):
            if hasattr(self, perm_method):
                is_authorized = getattr(self, perm_method)(user, perm, obj, from_user, from_groups)
                if is_authorized is not None:
                    break

        if is_authorized is not None:
            return is_authorized 
        else:
            return self.get_default_for_perm(perm)
    
    def get_all_permissions(self, user, obj, from_user=True, from_groups=True):
        """
        it returns all the permissions available for the total 
        permission list (self.perm) only if self.perm exists
        """
        allowed_permissions = []
        for perm in self.get_all_perms():
            if user.is_superuser or self.full_check(user, perm, obj, from_user, from_groups):
                allowed_permissions.append(perm)
        return set(allowed_permissions)
    
    """
    def get_group_permissions(self, user, obj):
        return self.get_all_permissions(user, obj, False, True)
    """
   
class DbGuard(Guard):
    obj_field = 'obj'
    user_field = 'user'
    group_field = 'group'
    
    def __init__(self, model, perms=None, default_perm=False):
        super(DbGuard, self).__init__(perms, default_perm)
        # TODO: accept model as string
        self.model = model
        self._cached_perms = None
    
    def get_all_perms(self):
        if self.perms is None:
            perms = {}
            for field in self.model._meta.fields:
                if isinstance(field, models.BooleanField):
                    perms.update({field.name: field.default})
            return perms
        else:
            return super(DbGuard, self).get_all_perms()
        
    def get_check_methods(self, perm):
        app_label, perm_name = self.unpack_perm(perm)
        return ('check', 'check_%s'%perm_name)
        
    def get_cached_perms(self, user, obj):
        if not self._cached_perms:
            qs = self.model.objects.order_by(self.user_field)\
             .filter(**{self.obj_field: obj})\
             .filter(models.Q(**{self.user_field: user}) | models.Q(**{"%s__user"%self.group_field: user}))
            self._cached_perms = list(qs)
        return self._cached_perms
    
    def clear_cached_perms(self):
        self._cached_perms = None
        
    def check(self, user, perm, obj, from_user, from_groups):
        is_authorized = None
        app_label, perm_name = self.unpack_perm(perm)
        field_names = self.model._meta.get_all_field_names()
        if perm_name in field_names:
            for cached_perm in self.get_cached_perms(user, obj):
                if from_groups and getattr(cached_perm, self.group_field):
                    is_authorized = getattr(cached_perm, perm_name)
                if from_user and getattr(cached_perm, self.user_field):
                    is_authorized = getattr(cached_perm, perm_name)
        
        return is_authorized
