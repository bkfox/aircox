import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from filer.fields.image import FilerImageField

from .. import settings


__all__ = ['Station', 'StationQuerySet', 'Port']


class StationQuerySet(models.QuerySet):
    def default(self, station=None):
        """
        Return station model instance, using defaults or
        given one.
        """
        if station is None:
            return self.order_by('-default', 'pk').first()
        return self.filter(pk=station).first()

    def active(self):
        return self.filter(active=True)


class Station(models.Model):
    """
    Represents a radio station, to which multiple programs are attached
    and that is used as the top object for everything.

    A Station holds controllers for the audio stream generation too.
    Theses are set up when needed (at the first access to these elements)
    then cached.
    """
    name = models.CharField(_('name'), max_length=64)
    slug = models.SlugField(_('slug'), max_length=64, unique=True)
    # FIXME: remove - should be decided only by Streamer controller + settings
    path = models.CharField(
        _('path'),
        help_text=_('path to the working directory'),
        max_length=256,
        blank=True,
    )
    default = models.BooleanField(
        _('default station'),
        default=True,
        help_text=_('use this station as the main one.')
    )
    active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('whether this station is still active or not.')
    )
    logo = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Logo'),
    )
    hosts = models.TextField(
        _("website's urls"), max_length=512, null=True, blank=True,
        help_text=_('specify one url per line')
    )
    audio_streams = models.TextField(
        _("audio streams"), max_length=2048, null=True, blank=True,
        help_text=_("Audio streams urls used by station's player. One url "
                    "a line.")
    )
    default_cover = FilerImageField(
        on_delete=models.SET_NULL,
        verbose_name=_('Default pages\' cover'), null=True, blank=True,
        related_name='+',
    )

    objects = StationQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, make_sources=True, *args, **kwargs):
        if not self.path:
            self.path = os.path.join(settings.AIRCOX_CONTROLLERS_WORKING_DIR,
                                     self.slug.replace('-', '_'))

        if self.default:
            qs = Station.objects.filter(default=True)
            if self.pk is not None:
                qs = qs.exclude(pk=self.pk)
            qs.update(default=False)

        super().save(*args, **kwargs)


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
        (TYPE_JACK, 'jack'), (TYPE_ALSA, 'alsa'),
        (TYPE_PULSEAUDIO, 'pulseaudio'), (TYPE_ICECAST, 'icecast'),
        (TYPE_HTTP, 'http'), (TYPE_HTTPS, 'https'),
        (TYPE_FILE, _('file'))
    )

    station = models.ForeignKey(
        Station, models.CASCADE, verbose_name=_('station'))
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

