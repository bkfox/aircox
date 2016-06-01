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
        auto_create = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.thread:
            if not self.title:
                self.title = _('{name} on {first_diff}').format(
                    self.related.program.name,
                    self.related.start.strftime('%A %d %B')
                )
            if not self.content:
                self.content = self.thread.content
            if not self.image:
                self.image = self.thread.image
            if not self.tags and self.pk:
                self.tags = self.thread.tags

