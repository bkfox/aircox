from enum import Enum, IntEnum

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy


class Output (models.Model):
    # Note: we don't translate the names since it is project names.
    class Type(IntEnum):
        jack = 0x00
        alsa = 0x01
        icecast = 0x02

    type = models.SmallIntegerField(
        _('output type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
        blank = True, null = True
    )
    settings = models.TextField(
        _('output settings'),
        help_text = _('list of comma separated params available; '
                      'this is put in the output config as raw code'),
        blank = True, null = True
    )


