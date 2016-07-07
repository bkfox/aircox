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


class Diffusion (cms.RelatedPost):
    actions = [actions.Play, actions.AddToPlaylist]

    class Relation:
        model = programs.Diffusion
        bindings = {
            'thread': 'program',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fill_empty()

    @property
    def info(self):
        if not self.related or not self.related.initial:
            return
        return _('rerun of %(day)s') % {
            'day': self.related.initial.start.strftime('%A %d/%m')
        }

