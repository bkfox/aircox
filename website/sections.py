import json

from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs
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
        qs = programs.Diffusion.get(
            now = True,
            type = programs.Diffusion.Type.normal
        )

        if not qs or not qs[0].is_date_in_my_range():
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

    def prepare_list(self, object_list):
        """
        This function just prepare the list of object, in order to:
        - have a good title
        - given a stream to listen to if needed
        """
        for post in object_list:
            # title
            if not hasattr(post, 'related') or \
                    not hasattr(post.related , 'program'):
                continue
            name = post.related.program.name
            if name not in post.title:
                post.title = ': ' + post.title if post.title else \
                            ' // ' + post.related.start.strftime('%A %d %B')
                post.title = name + post.title
        return object_list

    def get_object_list(self):
        diffs = self.get_diffs()

        posts = models.Diffusion.objects.filter(related__in = diffs)
        r = []
        for diff in diffs:
            diff_ = diff.initial if diff.initial else diff
            post = next((x for x in posts if x.related == diff_), None)
            if not post:
                post = sections.ListItem(date = diff.start)
            else:
                post = sections.ListItem(post=post)
                post.date = diff.start

            if diff.initial:
                post.info = _('rerun of %(day)s') % {
                    'day': diff.initial.start.strftime('%A %d/%m')
                }

            if self.object:
                post.update(self.object)
            else:
                thread = models.Program.objects. \
                            filter(related = diff.program, published = True)
                if thread:
                    post.update(thread[0])
            r.append(post)
        return [ sections.ListItem(post=post) for post in r ]

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
    List that add a navigation by date in its header.
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
        if self.date:
            return self.date
        elif self.kwargs and 'year' in self.kwargs:
            return tz.datetime(year = int(self.kwargs['year']),
                               month = int(self.kwargs['month']),
                               day = int(self.kwargs['day']),
                               hour = 0, minute = 0, second = 0,
                               microsecond = 0)
        return tz.now()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        date = self.date_or_default()
        dates = [ (date, self.get_date_url(date))
                    for date in self.nav_dates(date) ]

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
        return a url to the list for the given date
        """

    @property
    def url(self):
        return None


class Schedule(Diffusions,ListByDate):
    """
    Render a list of diffusions in the form of a schedule
    """
    fields = [ 'time', 'image', 'title', 'content', 'info', 'actions' ]
    truncate = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('schedule')

    def get_object_list(self):
        date = self.date_or_default()
        return routes.DateRoute.get_queryset(
            models.Diffusion, self.request, date.year, date.month,
            date.day
        ).order_by('date')

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
    Return a list of played stream sounds and diffusions.
    """
    @staticmethod
    def make_item(log):
        """
        Return a list of items to add to the playlist.
        """
        if issubclass(type(log.related), programs.Diffusion):
            diff = log.related
            post = models.Diffusion.objects.filter(related = diff).first() \
                    or models.Program.objects.filter(related = diff.program).first() \
                    or ListItem(title = diff.program.name)
            post.date = diff.start
            return post

        if issubclass(type(log.related), programs.Track):
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
        return []
        station = self.view.website.station
        qs = station.get_played(
            models = [ programs.Diffusion, programs.Track ],
        ).filter(
            date__year = int(year), date__month = int(month),
            date__day = int(day)
        )
        # TODO for each, exclude if there is a diffusion (that has not been logged)
        return [ cl.make_item(log) for log in qs ]

    @staticmethod
    def get_date_url(date):
        return 'TODO'

