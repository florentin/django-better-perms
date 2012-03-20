# -*- coding: utf-8 -*-
from django.db import models
from better_perms.models import CrudPermission
from better_perms.guards import DbGuard
from .guards import ArticleDbGuard, ArticleGuard


class Article(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    
    class Meta:
        db_table = 'better_perms__article'

    def __unicode__(self):
        return self.title

    def get_guard(self):
        if not hasattr(self, '_guard'):
            self._guard = ArticleDbGuard(model=ArticlePermission)
        return self._guard


class ArticlePermission(CrudPermission):
    obj = models.ForeignKey('Article')
    
    class Meta:
        db_table = 'better_perms__articlepermission'