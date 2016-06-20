import os
import stat
import logging

logger = logging.getLogger('aircox')

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.cms.models import Post, RelatedPost
import aircox.programs.models as programs


class Article (Post):
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


class Program (RelatedPost):
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


class Diffusion (RelatedPost):
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
        if self.thread:
            if not self.title:
                self.title = _('{name} // {first_diff}').format(
                    name = self.related.program.name,
                    first_diff = self.related.start.strftime('%A %d %B')
                )
            if not self.content:
                self.content = self.thread.content
            if not self.image:
                self.image = self.thread.image
            if not self.tags and self.pk:
                self.tags = self.thread.tags

    @property
    def info(self):
        if not self.related or not self.related.initial:
            return
        return _('rerun of %(day)s') % {
            'day': self.related.initial.start.strftime('%A %d/%m')
        }


class Sound (RelatedPost):
    """
    Publication concerning sound. In order to manage access of sound
    files in the filesystem, we use permissions -- it is up to the
    user to work select the correct groups and permissions.
    """
    embed = models.TextField(
        _('embedding code'),
        blank=True, null=True,
        help_text = _('HTML code used to embed a sound from an external '
                      'plateform'),
    )
    """
    Embedding code if the file has been published on an external
    plateform.
    """

    auto_chmod = True
    """
    change file permission depending on the "published" attribute.
    """
    chmod_flags = (stat.S_IRWXU, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH )
    """
    chmod bit flags, for (not_published, published)
    """
    class Relation:
        model = programs.Sound
        bindings = {
            'title': 'name',
            'date': 'mtime',
        }
        rel_to_post = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.auto_chmod and not self.related.removed and \
                os.path.exists(self.related.path):
            try:
                os.chmod(self.related.path,
                         self.chmod_flags[self.published])
            except PermissionError as err:
                logger.error(
                    'cannot set permission {} to file {}: {}'.format(
                        self.chmod_flags[self.published],
                        self.related.path, err
                    )
                )

