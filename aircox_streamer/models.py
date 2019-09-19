from django.db import models
from django.utils.translation import ugettext_lazy as _

from aircox.models import Station


__all__ = ['PortQuerySet', 'Port']


class PortQuerySet(models.QuerySet):
    def active(self, value=True):
        """ Active ports """
        return self.filter(active=value)

    def output(self):
        """ Filter in output ports """
        return self.filter(direction=Port.DIRECTION_OUTPUT)

    def input(self):
        """ Fitler in input ports """
        return self.filter(direction=Port.DIRECTION_INPUT)


class Port(models.Model):
    """
    Represent an audio input/output for the audio stream
    generation.

    You might want to take a look to LiquidSoap's documentation
    for the options available for each kind of input/output.

    Some port types may be not available depending on the
    direction of the port.
    """
    DIRECTION_INPUT = 0x00
    DIRECTION_OUTPUT = 0x01
    DIRECTION_CHOICES = ((DIRECTION_INPUT, _('input')),
                         (DIRECTION_OUTPUT, _('output')))

    TYPE_JACK = 0x00
    TYPE_ALSA = 0x01
    TYPE_PULSEAUDIO = 0x02
    TYPE_ICECAST = 0x03
    TYPE_HTTP = 0x04
    TYPE_HTTPS = 0x05
    TYPE_FILE = 0x06
    TYPE_CHOICES = (
        # display value are not translated becaused used as is in config
        (TYPE_JACK, 'jack'), (TYPE_ALSA, 'alsa'),
        (TYPE_PULSEAUDIO, 'pulseaudio'), (TYPE_ICECAST, 'icecast'),
        (TYPE_HTTP, 'http'), (TYPE_HTTPS, 'https'),
        (TYPE_FILE, 'file')
    )

    station = models.ForeignKey(
        Station, models.CASCADE, verbose_name=_('station'), related_name='+')
    direction = models.SmallIntegerField(
        _('direction'), choices=DIRECTION_CHOICES)
    type = models.SmallIntegerField(_('type'), choices=TYPE_CHOICES)
    active = models.BooleanField(
        _('active'), default=True,
        help_text=_('this port is active')
    )
    settings = models.TextField(
        _('port settings'),
        help_text=_('list of comma separated params available; '
                    'this is put in the output config file as raw code; '
                    'plugin related'),
        blank=True, null=True
    )

    objects = PortQuerySet.as_manager()

    def __str__(self):
        return "{direction}: {type} #{id}".format(
            direction=self.get_direction_display(),
            type=self.get_type_display(), id=self.pk or ''
        )

    def is_valid_type(self):
        """
        Return True if the type is available for the given direction.
        """

        if self.direction == self.DIRECTION_INPUT:
            return self.type not in (
                self.TYPE_ICECAST, self.TYPE_FILE
            )

        return self.type not in (
            self.TYPE_HTTP, self.TYPE_HTTPS
        )

    def save(self, *args, **kwargs):
        if not self.is_valid_type():
            raise ValueError(
                "port type is not allowed with the given port direction"
            )

        return super().save(*args, **kwargs)

