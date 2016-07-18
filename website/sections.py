import json
import datetime

from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs
import aircox.controllers.models as controllers
import aircox.cms.models as cms
import aircox.cms.routes as routes
import aircox.cms.sections as sections

from aircox.cms.exposures import expose
from aircox.cms.actions import Action

import aircox.website.models as models
import aircox.website.actions as actions
import aircox.website.utils as utils


@expose
class Player(sections.Section):
    """
    Display a player that is cool.
    """
    template_name = 'aircox/website/player.html'
    live_streams = []
    """
    ListItem objects that display a list of available streams.
    """
    #default_sounds

    @expose
    def on_air(cl, request):
        now = tz.now()
        qs = programs.Diffusion.objects.get_at(now).filter(
            type = programs.Diffusion.Type.normal
        )

        if not qs or not qs[0].is_date_in_range():
            return {}

        qs = qs[0]
        post = models.Diffusion.objects.filter(related = qs) or \
               models.Program.objects.filter(related = qs.program)
        if post:
            post = post[0]
        else:
            post = ListItem(title = qs.program.name)

        return {
            'item': post,
            'list': sections.List,
        }

    on_air._exposure.template_name = 'aircox/cms/list_item.html'

    @staticmethod
    def make_sound(post = None, sound = None):
        """
        Return a standard item from a sound that can be used as a
        player's item
        """
        r = {
            'title': post.title if post else sound.name,
            'url': post.url() if post else None,
            'info': utils.duration_to_str(sound.duration),
        }
        if sound.embed:
            r['embed'] = sound.embed
        else:
            r['stream'] = sound.url()
        return r

    @classmethod
    def get_recents(cl, count):
        """
        Return a list of count recent published diffusions that have sounds,
        as item usable in the playlist.
        """
        qs = models.Diffusion.objects \
                             .filter(published = True) \
                             .filter(related__end__lte = tz.datetime.now()) \
                             .order_by('-related__end')
        recents = []
        for post in qs:
            archives = post.related.get_archives()
            if not archives:
                continue

            archives = archives[0]
            recents.append(cl.make_sound(post, archives))
            if len(recents) >= count:
                break
        return recents

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'base_template': 'aircox/cms/section.html',
            'live_streams': self.live_streams,
            'recents': self.get_recents(10),
        })
        return context


class Diffusions(sections.List):
    """
    Section that print diffusions. When rendering, if there is no post yet
    associated, use the programs' article.
    """
    order_by = '-start'
    show_schedule = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_diffs(self, **filter_args):
        qs = programs.Diffusion.objects.filter(
            type = programs.Diffusion.Type.normal
        )
        if self.object:
            obj = self.object.related
            obj_type = type(obj)
            if obj_type == programs.Program:
                qs = qs.filter(program = obj)
            elif obj_type == programs.Diffusion:
                if obj.initial:
                    obj = obj.initial
                qs = qs.filter(initial = obj) | qs.filter(pk = obj.pk)
        if filter_args:
            qs = qs.filter(**filter_args).order_by('start')

        return qs

        #r = []
        #if self.next_count:
        #    r += list(programs.Diffusion.get(next=True, queryset = qs)
        #                .order_by('-start')[:self.next_count])
        #if self.prev_count:
        #    r += list(programs.Diffusion.get(prev=True, queryset = qs)
        #                .order_by('-start')[:self.prev_count])
        #return r

    def get_object_list(self):
        diffs = self.get_diffs().order_by('start')
        return models.Diffusion.objects.get_for(diffs)

    @property
    def url(self):
        if not self.need_url():
            return

        if self.object:
            return models.Diffusion.reverse(routes.ThreadRoute,
                pk = self.object.id,
                thread_model = 'program',
            )
        return models.Diffusion.reverse(routes.AllRoute)

    @property
    def header(self):
        if not self.show_schedule:
            return None

        def str_sched(sched):
            info = ' <span class="info">(' + _('rerun of %(day)s') % {
                'day': sched.initial.date.strftime('%A')
            } + ')</span>' if sched.initial else ''

            text = _('%(day)s at %(time)s, %(freq)s') % {
                'day': sched.date.strftime('%A'),
                'time': sched.date.strftime('%H:%M'),
                'freq': sched.get_frequency_display(),
            }
            return text + info

        return ' / \n'.join([str_sched(sched)
                 for sched in programs.Schedule.objects \
                    .filter(program = self.object and self.object.related.pk)
        ])


class Playlist(sections.List):
    title = _('Playlist')
    message_empty = ''

    def get_object_list(self):
        tracks = programs.Track.get_for(object = self.object.related) \
                     .order_by('position')
        return [ sections.ListItem(title=track.title, content=track.artist)
                    for track in tracks ]


class Sounds(sections.List):
    title = _('Podcasts')

    def get_object_list(self):
        if self.object.related.end > tz.make_aware(tz.datetime.now()):
            return

        sounds = programs.Sound.objects.filter(
            diffusion = self.object.related,
            public = True,
        ).order_by('type')
        return [
            sections.ListItem(
                title=sound.name,
                info=utils.duration_to_str(sound.duration),
                sound = sound,
                actions = [ actions.AddToPlaylist, actions.Play ],
            ) for sound in sounds
        ]


class ListByDate(sections.List):
    """
    List that add a navigation by date in its header. It aims to be
    used with DateRoute.
    """
    template_name = 'aircox/website/list_by_date.html'
    message_empty = ''

    model = None

    date = None
    """
    date of the items to print
    """
    nav_days = 7
    """
    number of days to display in the header
    """
    nav_date_format = '%a. %d'
    """
    format of dates to display in the header
    """
    nav_per_week = True
    """
    if true, print days in header by week
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_css_class('list_by_date')

    def nav_dates(self, date):
        """
        Return a list of dates of the week of the given date.
        """
        first = int((self.nav_days - 1) / 2)
        first = date - tz.timedelta(days=date.weekday()) \
                if self.nav_per_week else \
                date - tz.timedelta(days=first)
        return [ first + tz.timedelta(days=i) for i in range(0, self.nav_days) ]

    def date_or_default(self):
        """
        Return self.date or create a date if needed, using kwargs'
        year, month, day attributes if exists (otherwise, use today)
        """
        if self.date:
            return datetime.date(self.date)
        elif self.kwargs and 'year' in self.kwargs:
            return datetime.date(
                year = int(self.kwargs['year']),
                month = int(self.kwargs['month']),
                day = int(self.kwargs['day'])
            )
        return datetime.date.today()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        date = self.date_or_default()
        dates = [ (date, self.get_date_url(date))
                    for date in self.nav_dates(date) ]

        # FIXME
        next_week = dates[-1][0] + tz.timedelta(days=1)
        next_week = self.get_date_url(next_week)

        prev_week = dates[0][0] - tz.timedelta(days=1)
        prev_week = self.get_date_url(prev_week)

        context.update({
            'nav': {
                'date': date,
                'dates': dates,
                'next': next_week,
                'prev': prev_week,
            }
        })
        return context

    @staticmethod
    def get_date_url(date):
        """
        return an url for the given date
        """
        return self.view.website.reverse(
            model = self.model, route = routes.DateRoute,
            year = date.year, month = date.month, day = date.day,
        )

    @property
    def url(self):
        return None

class Schedule(Diffusions,ListByDate):
    """
    Render a list of diffusions in the form of a schedule
    """
    model = models.Diffusion
    fields = [ 'time', 'image', 'title', 'content', 'info', 'actions' ]
    truncate = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('schedule')

    def get_object_list(self):
        date = self.date_or_default()
        diffs = programs.Diffusion.objects.get_at(date).order_by('start')
        return models.Diffusion.objects.get_for(diffs, create = True)

    @staticmethod
    def get_date_url(date):
        """
        return an url for the given date
        """
        return models.Diffusion.reverse(
            routes.DateRoute,
            year = date.year, month = date.month, day = date.day,
        )


class Logs(ListByDate):
    """
    Print a list of played stream tracks and diffusions.
    Note that for the moment we don't print if the track has been
    partially hidden by a scheduled diffusion
    """
    model = controllers.Log

    @staticmethod
    def make_item(item):
        """
        Return a list of items to add to the playlist.
        Only support Log related to a Track and programs.Diffusion
        """
        if issubclass(type(item), programs.Diffusion):
            return models.Diffusion.objects.get_for(
                item, create = True, save = False
            )

        track = log.related
        post = ListItem(
            title = '{artist} &#8212; {name}'.format(
                artist = track.artist,
                name = track.name,
            ),
            date = log.date,
            content = track.info,
            info = '♫',
        )
        return post

    def get_object_list(self):
        date = self.date_or_default()
        if date > datetime.date.today():
            return []

        logs = controllers.Log.get_for(model = programs.Track) \
                              .filter(date__contains = date) \
                              .order_by('date')

        diffs = programs.Diffusion.objects.get_at(date) \
                        .filter(type = programs.Diffusion.Type.normal)

        items = []
        prev_diff = None
        for diff in diffs:
            logs_ = logs.filter(date__gt = prev_diff.end,
                                date__lt = diff.start) \
                    if prev_diff else \
                    logs.filter(date__lt = diff.start)
            prev_diff = diff
            items.extend(logs_)
            items.append(diff)

        return list(map(self.make_item, items))


