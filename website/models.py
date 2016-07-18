import os
import stat
import logging

logger = logging.getLogger('aircox')

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs
import aircox.cms.models as cms
import aircox.website.actions as actions


class Article (cms.Post):
    """
    Represent an article or a static page on the website.
    """
    static_page = models.BooleanField(
        _('static page'),
        default = False,
    )
    focus = models.BooleanField(
        _('article is focus'),
        default = False,
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')


class Program (cms.RelatedPost):
    website = models.URLField(
        _('website'),
        blank=True, null=True
    )
    # rss = models.URLField()
    email = models.EmailField(
        _('email'), blank=True, null=True,
        help_text=_('contact address, stays private')
    )

    class Relation:
        model = programs.Program
        bindings = {
            'title': 'name',
        }
        rel_to_post = True
        auto_create = True


class DiffusionManager(models.Manager):
    @staticmethod
    def post_or_default(diff, post, create = True, save = False):
        if not post and create:
            post = Diffusion(related = diff.initial or diff)
            if save:
                post.save()
            else:
                post.rel_to_post()
        if post:
            post.date = diff.start
            post.related = diff
        return post

    def get_for(self, diffs, create = True, save = False):
        """
        Get posts for the given related diffusion. Return a list
        not a Queryset, ordered following the given list.

        Update the post objects to make date corresponding to the
        diffusions.

        - diffs: a programs.Diffusion, or iterable of
            programs.Diffusion. In the first case, return
            an object instead of a list
        - create: create a post for each Diffusion if missing
        - save: save the created posts
        """
        if not hasattr(diffs, '__iter__'):
            qs = self.filter(related = diffs.initial or diff,
                             published = True)
            return post_or_default(diffs, post, create, save)

        qs = self.filter(related__in = [
            diff.initial or diff for diff in diffs
        ], published = True)
        posts = []
        for diff in diffs:
            post = qs.filter(related = diff.initial or diff).first()
            post = self.post_or_default(diff, post, create, save)
            if post:
                posts.append(post)
        return posts


class Diffusion(cms.RelatedPost):
    objects = DiffusionManager()
    actions = [actions.Play, actions.AddToPlaylist]

    class Relation:
        model = programs.Diffusion
        bindings = {
            'thread': 'program',
            'title': lambda post, rel: rel.program.name,
            'date': 'start',
        }
        fields_args = {
            'limit_choice_to': {
                'initial': None
            }
        }
        rel_to_post = True

        def auto_create(object):
            return not object.initial

    def __init__(self, *args, rel_to_post = False, **kwargs):
        super().__init__(*args, **kwargs)
        if rel_to_post and self.related:
            self.rel_to_post()

        self.fill_empty()
        if not self.subtitle:
            self.subtitle = _('Diffusion of the %(date)s') % {
                'date': self.related.start.strftime('%A %d/%m')
            }

    @property
    def info(self):
        if not self.related or not self.related.initial:
            return
        return _('rerun of %(day)s') % {
            'day': self.related.initial.start.strftime('%A %d/%m')
        }

    def url(self):
        url = super().url()
        if url or not self.related.initial:
            return url

        post = Diffusions.objects.filter(related = self.related.initial) \
                                 .first()
        return post.url() if post else ''



