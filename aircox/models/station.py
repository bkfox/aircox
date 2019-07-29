from enum import IntEnum
import os

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

import aircox.settings as settings


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
    path = models.CharField(
        _('path'),
        help_text=_('path to the working directory'),
        max_length=256,
        blank=True,
    )
    default = models.BooleanField(
        _('default station'),
        default=True,
        help_text=_('if checked, this station is used as the main one')
    )

    objects = StationQuerySet.as_manager()

    #
    # Controllers
    #
    __sources = None
    __dealer = None
    __streamer = None

    def __prepare_controls(self):
        import aircox.controllers as controllers
        from .program import Program
        if not self.__streamer:
            self.__streamer = controllers.Streamer(station=self)
            self.__dealer = controllers.Source(station=self)
            self.__sources = [self.__dealer] + [
                controllers.Source(station=self, program=program)

                for program in Program.objects.filter(stream__isnull=False)
            ]

    @property
    def inputs(self):
        """
        Return all active input ports of the station
        """
        return self.port_set.filter(
            direction=Port.Direction.input,
            active=True
        )

    @property
    def outputs(self):
        """ Return all active output ports of the station """
        return self.port_set.filter(
            direction=Port.Direction.output,
            active=True,
        )

    @property
    def sources(self):
        """ Audio sources, dealer included """
        self.__prepare_controls()
        return self.__sources

    @property
    def dealer(self):
        """ Get dealer control """
        self.__prepare_controls()
        return self.__dealer

    @property
    def streamer(self):
        """ Audio controller for the station """
        self.__prepare_controls()
        return self.__streamer

    def __str__(self):
        return self.name

    def save(self, make_sources=True, *args, **kwargs):
        if not self.path:
            self.path = os.path.join(
                settings.AIRCOX_CONTROLLERS_WORKING_DIR,
                self.slug
            )

        if self.default:
            qs = Station.objects.filter(default=True)

            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(default=False)

        super().save(*args, **kwargs)


class Port (models.Model):
    """
    Represent an audio input/output for the audio stream
    generation.

    You might want to take a look to LiquidSoap's documentation
    for the options available for each kind of input/output.

    Some port types may be not available depending on the
    direction of the port.
    """
    class Direction(IntEnum):
        input = 0x00
        output = 0x01

    class Type(IntEnum):
        jack = 0x00
        alsa = 0x01
        pulseaudio = 0x02
        icecast = 0x03
        http = 0x04
        https = 0x05
        file = 0x06

    station = models.ForeignKey(
        Station,
        verbose_name=_('station'),
        on_delete=models.CASCADE,
    )
    direction = models.SmallIntegerField(
        _('direction'),
        choices=[(int(y), _(x)) for x, y in Direction.__members__.items()],
    )
    type = models.SmallIntegerField(
        _('type'),
        # we don't translate the names since it is project names.
        choices=[(int(y), x) for x, y in Type.__members__.items()],
    )
    active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('this port is active')
    )
    settings = models.TextField(
        _('port settings'),
        help_text=_('list of comma separated params available; '
                    'this is put in the output config file as raw code; '
                    'plugin related'),
        blank=True, null=True
    )

    def is_valid_type(self):
        """
        Return True if the type is available for the given direction.
        """

        if self.direction == self.Direction.input:
            return self.type not in (
                self.Type.icecast, self.Type.file
            )

        return self.type not in (
            self.Type.http, self.Type.https
        )

    def save(self, *args, **kwargs):
        if not self.is_valid_type():
            raise ValueError(
                "port type is not allowed with the given port direction"
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        return "{direction}: {type} #{id}".format(
            direction=self.get_direction_display(),
            type=self.get_type_display(),
            id=self.pk or ''
        )



