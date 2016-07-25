"""
Classes that define common interfaces in order to control external
software that generate the audio streams for us, such as Liquidsoap.

It must be implemented per program in order to work.


Basically, we follow the follow the idea that a Station has different
sources that are used to generate the audio stream:
- **stream**: one source per Streamed program;
- **dealer**: one source for all Scheduled programs;
- **master**: main output
"""
import os
import datetime
import logging
from enum import IntEnum

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs
from aircox.programs.utils import to_timedelta
import aircox.controllers.settings as settings
from aircox.controllers.plugins.plugins import Plugins


logger = logging.getLogger('aircox.controllers')

Plugins.discover()


class Station(programs.Nameable):
    path = models.CharField(
        _('path'),
        help_text = _('path to the working directory'),
        max_length = 256,
        blank = True,
    )
    plugin_name = models.CharField(
        _('plugin'),
        max_length = 32,
        choices = [ (name, name) for name in Plugins.registry.keys() ],
    )
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('this station is active')
    )

    plugin = None
    """
    The plugin used for this station. This is initialized at __init__,
    based on self.plugin_name and should not be changed.
    """
    controller = None
    """
    Controllers over the station. It is implemented by the plugin using
    plugin.StationController
    """

    @property
    def id_(self):
        return self.slug

    def get_sources(self, type = None, prepare = True, dealer = False):
        """
        Return a list of active sources that can have their controllers
        initialized.
        """
        qs = self.source_set.filter(active = True)
        if type:
            qs = qs.filter(type = type)

        sources = [ source.prepare() or source for source in qs ]
        if dealer == True:
            sources.append(self.dealer)
        return sources

    @property
    def stream_sources(self):
        return self.get_sources(type = Source.Type.stream)

    @property
    def file_sources(self):
        return self.get_sources(type = Source.Type.file)

    @property
    def fallback_sources(self):
        return self.get_sources(type = Source.Type.fallback)

    @property
    def outputs(self):
        """
        List of active outputs
        """
        return [ output for output in self.output_set.filter(active = True) ]

    def prepare(self, fetch = True):
        """
        Initialize station's controller. Does not initialize sources'
        controllers.

        Note that the Station must have been saved first, in order to
        have correct informations such as the working path.
        """
        if not self.pk:
            raise ValueError('station be must saved first')

        self.controller = self.plugin.init_station(self)
        self.dealer.prepare()
        for source in self.source_set.all():
            source.prepare()
        if fetch:
            self.controller.fetch()

    def make_sources(self):
        """
        Generate default sources for the station and save them.
        """
        streams = programs.Program.objects.filter(
            active = True, stream__isnull = False
        )
        for stream in streams:
            Source(station = self,
                   type = Source.Type.stream,
                   name = stream.name,
                   program = stream).save()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dealer = Source(
            station = self,
            name = _('Dealer'),
            type = Source.Type.dealer
        )

        if self.plugin_name:
            self.plugin = Plugins.registry.get(self.plugin_name)

    def get_played(self, models, archives = True):
        """
        Return a queryset with log of played elements on this station,
        of the given models, ordered by date ascending.

        * model: a model or a list of models
        * archive: if false, exclude log of diffusion's archives from
            the queryset;
        """
        qs = Log.objects.get_for(model = models) \
                .filter(station = self, type = Log.Type.play)
        if not archives and self.dealer:
            qs = qs.exclude(
                source = self.dealer.id_,
                related_type = ContentType.objects.get_for_model(
                    programs.Sound
                )
            )
        return qs.order_by('date')


    @staticmethod
    def __mix_logs_and_diff(diffs, logs, count = 0):
        """
        Mix together logs and diffusion items ordering by their date.
        Diffs and Logs are assumed to be ordered by -date, and so is
        the resulting list
        """
        # we fill a list with diff and retrieve logs that happened between
        # each to put them too there
        items = []
        diff_ = None
        for diff in diffs:
            logs_ = \
                logs.filter(date__gt = diff.end, date__lt = diff_.start) \
                    if diff_ else logs.filter(date__gt = diff.end)
            diff_ = diff
            items.extends(logs_)
            items.append(diff)
            if count and len(items) >= count:
                break

        if diff_ and not count or len(items) <= count:
            logs_ = logs.filter(date__lt = diff_.end)
            items.extend(logs_)

        return items[:count] if count else items


    def on_air(self, date = None, count = 0):
        """
        Return a list of what happened on air, based on logs and
        diffusions informations. The list is sorted by -date.

        * date: only for what happened on this date;
        * count: number of items to retrieve if not zero;

        Be careful with what you which for: the result is a plain list.

        The list contains:
        * track logs: for the streamed programs;
        * diffusion: for the scheduled diffusions;
        """
        # FIXME: as an iterator?
        # TODO argument to get sound instead of tracks
        # TODO #Station
        date = date or tz.now().date()
        if date > datetime.date.today():
            return []

        logs = Log.objects.get_for(model = programs.Track) \
                  .filter(station = self) \
                  .order_by('-date')
        diffs = programs.Diffusion.objects \
                    .filter(type = Diffusion.Type.normal) \
                    .order_by('-date')
        if date:
            logs = logs.filter(date__contains = date)
            diffs = diffs.get_at(date)
        return self.__mix_logs_and_diff(diffs, logs, count)


    def save(self, make_sources = True, *args, **kwargs):
        """
        * make_sources: if the model has not been yet saved, generate
            sources for it.
        """
        if not self.path:
            self.path = os.path.join(
                settings.AIRCOX_CONTROLLERS_MEDIA,
                self.slug
            )

        super().save(*args, **kwargs)

        if make_sources and not self.source_set.count():
            self.make_sources()
            self.prepare()

        # test
        self.prepare()
        self.controller.push()

class Source(programs.Nameable):
    """
    Source designate a source for the audio stream.

    A Source can have different types, that are declared here by order
    of priority. A lower value priority means that the source has a higher
    priority.
    """
    class Type(IntEnum):
        file = 0x01
        """
        Use a file as input, that can either be a local or distant file.
        Path must be set.

        Should be used only for exceptional cases, such as streaming from
        distant place.
        """
        dealer = 0x02
        """
        This source is used for scheduled programs. It is automatically
        added to the station, and may not be saved.
        """
        stream = 0x03
        """
        Source related to a streamed programs (one for each). programs.Program
        must be set in this case.
        It uses program's stream information in order to generate correct
        delays or time ranges.
        """
        fallback = 0x05
        """
        Same as file, but declared with a lower priority than streams.
        Their goal is to be used when no other source is available, so
        it is NOT interactive.
        """

    station = models.ForeignKey(
        Station,
        verbose_name = _('station'),
    )
    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
    )
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('this source is active')
    )
    program = models.ForeignKey(
        programs.Program,
        verbose_name = _('related program'),
        blank = True, null = True
    )
    url = models.TextField(
        _('url'),
        blank = True, null = True,
        help_text = _('url related to a file local or distant')
    )

    controller = None
    """
    Implement controls over a Source. This is done by the plugin, that
    implements plugin.SourceController;
    """

    @property
    def id_(self):
        return self.slug

    @property
    def stream(self):
        if self.type != self.Type.stream or not self.program:
            return
        return self.program.stream_set and self.program.stream_set.first()

    def prepare(self, fetch = True):
        """
        Create a controller
        """
        self.controller = self.station.plugin.init_source(self)
        if fetch:
            self.controller.fetch()

    def load_playlist(self, diffusion = None, program = None):
        """
        Load a playlist to the controller. If diffusion or program is
        given use it, otherwise, try with self.program if exists, or
        (if URI, self.value).

        A playlist from a program uses all archives available for the
        program.
        """
        if diffusion:
            self.controller.playlist = diffusion.playlist
            return

        program = program or self.program
        if program:
            self.controller.playlist = [ sound.path for sound in
                programs.Sound.objects.filter(
                    type = programs.Sound.Type.archive,
                    removed = False,
                    path__startswith = program.path
                )
            ]
            return

        if self.type == self.Type.file and self.value:
            self.controller.playlist = [ self.value ]
            return

    def save(self, *args, **kwargs):
        if self.type in (self.Type.file, self.Type.fallback) and \
                not self.url:
            raise ValueError('url is missing but required')
        if self.type == self.Type.stream and \
                (not self.program or not self.program.stream_set.count()):
            raise ValueError('missing related stream program; program must be '
                             'a streamed program')
        if self.type == self.Type.dealer:
            raise ValueError('can not save a dealer source')

        super().save(*args, **kwargs)


class Output (models.Model):
    class Type(IntEnum):
        jack = 0x00
        alsa = 0x01
        icecast = 0x02

    station = models.ForeignKey(
        Station,
        verbose_name = _('station'),
    )
    type = models.SmallIntegerField(
        _('type'),
        # we don't translate the names since it is project names.
        choices = [ (int(y), x) for x,y in Type.__members__.items() ],
    )
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('this output is active')
    )
    settings = models.TextField(
        _('output settings'),
        help_text = _('list of comma separated params available; '
                      'this is put in the output config as raw code; '
                      'plugin related'),
        blank = True, null = True
    )


class Log(programs.Related):
    """
    Log sounds and diffusions that are played on the station.

    This only remember what has been played on the outputs, not on each
    track; Source designate here which source is responsible of that.
    """
    class Type(IntEnum):
        stop = 0x00
        """
        Source has been stopped (only when there is no more sound)
        """
        play = 0x01
        """
        Source has been started/changed and is running related_object
        If no related_object is available, comment is used to designate
        the sound.
        """
        load = 0x02
        """
        Source starts to be preload related_object
        """
        other = 0x03
        """
        Other log
        """

    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
        blank = True, null = True,
    )
    station = models.ForeignKey(
        Station,
        verbose_name = _('station'),
        help_text = _('station on which the event occured'),
    )
    source = models.CharField(
        # we use a CharField to avoid loosing logs information if the
        # source is removed
        _('source'),
        max_length=64,
        help_text = _('source id that make it happen on the station'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        auto_now_add=True,
    )
    comment = models.CharField(
        _('comment'),
        max_length = 512,
        blank = True, null = True,
    )

    @property
    def end(self):
        """
        Calculated end using self.related informations
        """
        if self.related_type == programs.Diffusion:
            return self.related.end
        if self.related_type == programs.Sound:
            return self.date + to_timedelta(self.duration)
        return self.date

    def is_expired(self, date = None):
        """
        Return True if the log is expired. Note that it only check
        against the date, so it is still possible that the expiration
        occured because of a Stop or other source.
        """
        date = programs.date_or_default(date)
        return self.end < date

    def print(self):
        logger.info('log #%s: %s%s',
            str(self),
            self.comment or '',
            ' -- {} #{}'.format(self.related_type, self.related_id)
                if self.related else ''
        )

    def __str__(self):
        return '#{} ({}, {})'.format(
                self.pk, self.date.strftime('%Y/%m/%d %H:%M'), self.source
        )



