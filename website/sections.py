from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.programs.models as programs
import aircox.cms.models as cms
import aircox.cms.routes as routes
import aircox.cms.sections as sections

import aircox.website.models as models


class Diffusions(sections.List):
    """
    Section that print diffusions. When rendering, if there is no post yet
    associated, use the programs' article.
    """
    next_count = 5
    prev_count = 5
    show_schedule = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)

    def get_diffs(self, **filter_args):
        qs = programs.Diffusion.objects.filter(
            type = programs.Diffusion.Type.normal
        )
        if self.object:
            qs = qs.filter(program = self.object.related)
        if filter_args:
            qs = qs.filter(**filter_args).order_by('start')

        r = []
        if self.next_count:
            r += list(programs.Diffusion.get(next=True, queryset = qs)
                        .order_by('-start')[:self.next_count])
        if self.prev_count:
            r += list(programs.Diffusion.get(prev=True, queryset = qs)
                        .order_by('-start')[:self.prev_count])
        return r

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
                    'day': diff.initial.date.strftime('%A %d/%m')
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
        if self.object:
            return models.Diffusion.route_url(routes.ThreadRoute,
                pk = self.object.id,
                thread_model = 'program',
            )
        return models.Diffusion.route_url(routes.AllRoute)

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
                    .filter(program = self.object.related.pk)
        ])


class Playlist(sections.List):
    title = _('Playlist')
    message_empty = ''

    def get_object_list(self):
        tracks = programs.Track.objects \
                     .filter(diffusion = self.object.related) \
                     .order_by('position')
        return [ sections.ListItem(title=track.title, content=track.artist)
                    for track in tracks ]


class Schedule(Diffusions):
    """
    Render a list of diffusions in the form of a schedule
    """
    template_name = 'aircox/website/schedule.html'
    date = None
    days = 7
    nav_date_format = '%a. %d'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('schedule')

    @staticmethod
    def get_week_dates(date):
        first = date - tz.timedelta(days=date.weekday())
        return [ first + tz.timedelta(days=i) for i in range(0, 7) ]

    def date_or_default(self):
        if self.date:
            return self.date
        elif 'year' in self.kwargs:
            return tz.datetime(year = int(self.kwargs['year']),
                               month = int(self.kwargs['month']),
                               day = int(self.kwargs['day']),
                               hour = 0, minute = 0, second = 0,
                               microsecond = 0)
        return tz.datetime.now()

    def get_diffs(self):
        date = self.date_or_default()
        return super().get_diffs(
            start__year = date.year,
            start__month = date.month,
            start__day = date.day,
        )

    def get_context_data(self, **kwargs):
        date = self.date_or_default()
        dates_url = [
            (date, models.Diffusion.route_url(
                routes.DateRoute,
                year = date.year, month = date.month, day = date.day
            ))
            for date in self.get_week_dates(date)
        ]

        context = super().get_context_data(**kwargs)
        context.update({
            'date': date,
            'dates_url': dates_url,
        })
        return context


#class DatesOfDiffusion(sections.List):
#    title = _('Dates of diffusion')
#
#    def get_object_list(self):
#        diffs = list(programs.Diffusion.objects. \
#            filter(initial = self.object.related). \
#            exclude(type = programs.Diffusion.Type.unconfirmed)
#        )
#        diffs.append(self.object.related)
#
#        items = []
#        for diff in sorted(diffs, key = lambda d: d.date, reverse = True):
#            info = ''
#            if diff.initial:
#                info = _('rerun')
#            if diff.type == programs.Diffusion.Type.canceled:
#                info += ' ' + _('canceled')
#            items.append(
#                sections.List.Item(None, diff.start.strftime('%c'), info, None,
#                                   'canceled')
#            )
#        return items
#
## TODO sounds
#

