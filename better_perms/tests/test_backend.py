__author__ = 'florentin.sardan'

import sys
from django.test import TestCase, TransactionTestCase
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import DEFAULT_DB_ALIAS
from django.contrib.auth.models import User, Group, AnonymousUser
from better.perms.exceptions import ObjectPermissionException, GuardException
from .models import Article, ArticlePermission
from .guards import ArticleGuard
  
class MixinTestCase(object): # TestCase TransactionTestCase
    apps = ('better.perms.tests', )
    
    def _pre_setup(self):
        # Call the original method that does the fixtures etc.
        super(MixinTestCase, self)._pre_setup()
        
        # Add the models to the db.
        self._original_installed_apps = list(settings.INSTALLED_APPS)
        for app in self.apps:
            settings.INSTALLED_APPS.append(app)
        loading.cache.loaded = False
        call_command('syncdb', **{'verbosity': 0, 
                                  'database': DEFAULT_DB_ALIAS,
                                  'interactive': False,
                                  'load_initial_data': False,
                                  })
        

    def _post_teardown(self):
        # Call the original method.
        super(MixinTestCase, self)._post_teardown()
        # Restore the settings.
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False
    
    def setUp(self):
        self.mike = User.objects.create(username="mike", is_active=True)
        self.anonym = AnonymousUser()
        self.manager = Group.objects.create(name="manager")
        self.article1 = Article.objects.create(title='test article')
        self.mike.groups.add(self.manager)
        """
        myuser.groups = [group_list]
        myuser.groups.add(group, group, ...)
        myuser.groups.remove(group, group, ...)
        myuser.groups.clear()
        myuser.user_permissions = [permission_list]
        myuser.user_permissions.add(permission, permission, ...)
        myuser.user_permissions.remove(permission, permission, ...)
        myuser.user_permissions.clear()
        """
    
    def tearDown(self):
        self.mike.delete()
        self.article1.delete()
        self.manager.delete()


class BaseTestCase(MixinTestCase, TestCase):
    pass


class TransBaseTestCase(MixinTestCase, TransactionTestCase):
    def _fixture_setup(self):
        pass


class BackendTest(BaseTestCase): #TransBaseTestCase
    def test_has_perm(self):
        self.assertFalse(self.mike.has_perm('create_obj', self.article1))
        self.assertFalse(self.mike.has_perm('read_obj'))
        self.assertTrue(self.mike.has_perm('read_obj', self.article1))
        self.assertRaises(GuardException, self.mike.has_perm, 'read-obj', self.article1)
        
        perm1 = ArticlePermission.objects.create(user=self.mike, obj=self.article1, 
                                                 create_obj=True, 
                                                 read_obj=False, 
                                                 update_obj=False)
        
        self.assertTrue(self.mike.has_perm('create_obj', self.article1))
        self.assertFalse(self.mike.has_perm('read_obj', self.article1))
        self.assertFalse(self.mike.has_perm('update_obj', self.article1))
        self.assertFalse(self.mike.has_perm('delete_obj', self.article1))
        self.assertEqual(self.mike.get_all_permissions(self.article1), set(['create_obj']))
        
        self.mike.is_active = False
        self.assertFalse(self.mike.has_perm('create_obj', self.article1))
        self.assertFalse(self.anonym.has_perm('create_obj', self.article1))
        
        self.mike.is_active = True
        
        
        perm2 = ArticlePermission.objects.create(group=self.manager, obj=self.article1, 
                                                create_obj=True,
                                                read_obj=False,
                                                update_obj=True)
        
        # user permissions have priority
        self.assertTrue(self.mike.has_perm('create_obj', self.article1))
        self.assertFalse(self.mike.has_perm('read_obj', self.article1))
        self.assertFalse(self.mike.has_perm('update_obj', self.article1))

        perm1.delete()
        self.article1._guard.clear_cached_perms()

        self.assertTrue(self.mike.has_perm('create_obj', self.article1))
        self.assertFalse(self.mike.has_perm('read_obj', self.article1))
        self.assertTrue(self.mike.has_perm('update_obj', self.article1))
        perm2.delete()

    def test_guards(self):
        self.article1._guard = None
        self.assertRaises(ObjectPermissionException, self.mike.has_perm, 'read_obj', self.article1)
        
        self.article1._guard = ArticleGuard()
        self.assertFalse(self.mike.has_perm('create_obj', self.article1))
        self.assertTrue(self.mike.has_perm('read_obj', self.article1))
        
# TODO
# test for app_label.permissions_name
# test for invalid permissions names: mod#le.n@ame
