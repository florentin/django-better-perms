from django.db import models
from django.contrib.auth.models import User, Group

class Permission(models.Model):
    """
    The subclass must add the obj reference field:
        obj = models.ForeignKey(ReferredModel)
    and the permission columns:
        view_obj = models.BooleanField('Can view')
    
    The referred model must have this method:
        def get_guard(self):
            return Guard(model=ArticlePermission)
    """
    user = models.ForeignKey(User, blank=True, null=True, unique=True)
    group = models.ForeignKey(Group, blank=True, null=True, unique=True)
    
    class Meta:
        abstract = True


class CrudPermission(Permission):
    create_obj = models.NullBooleanField('Can create')
    read_obj = models.NullBooleanField('Can read')
    update_obj = models.NullBooleanField('Can update')
    delete_obj = models.NullBooleanField('Can delete')
    
    class Meta:
        abstract = True
