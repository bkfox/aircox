from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.cms.models import RelatedPost, Article
import aircox.programs.models as programs

class Program (RelatedPost):
    url = models.URLField(_('website'), blank=True, null=True)
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
                    self.related.program.name,
                    self.related.start.strftime('%A %d %B')
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
