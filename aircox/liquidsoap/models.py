from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs


class Output (models.Model):
    # Note: we don't translate the names since it is project names.
    Type = {
        'jack': 0x00,
        'alsa': 0x01,
        'icecast': 0x02,
    }

    station = models.ForeignKey(
        programs.Station,
        verbose_name = _('station'),
    )
    type = models.SmallIntegerField(
        _('output type'),
        choices = [ (y, x) for x,y in Type.items() ],
        blank = True, null = True
    )
    settings = models.TextField(
        _('output settings'),
        help_text = _('list of comma separated params available; '
                      'this is put in the output config as raw code'),
        blank = True, null = True
    )


