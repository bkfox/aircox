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
    Schedule printing diffusions starting at the given date

    * date: if set use this date instead of now;
    * days: number of days to show;
    * time_format: force format of the date in schedule header;
    """
    date = None
    days = 7
    time_format = '%a. %d'

    def get_diffs(self):
        date = self.date or tz.datetime.now()
        return super().get_diffs(
            start__year = date.year,
            start__month = date.month,
            start__day = date.day,
        )

    @property
    def header(self):
        date = self.date or tz.datetime.now()
        date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        curr = date - tz.timedelta(days=date.weekday())
        last = curr + tz.timedelta(days=7)

        r = """
        <script>function update_schedule(url, event) {
            var target = event.currentTarget;

            while(target && target.className.indexOf('section'))
                target = target.parentNode;

            if(!target)
                return false;


            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if(xhr.readyState != 4 || xhr.status != 200 && xhr.status)
                    return;

                var obj = document.createElement('div');
                obj.innerHTML = xhr.responseText;
                obj = obj.getElementsByTagName('ul');
                console.log(obj)
                if(!obj)
                    return;

                obj = obj[0];
                target.replaceChild(obj, target.querySelector('ul'))
                target.querySelector('nav a').href = url
            }

            xhr.open('GET', url + '?embed=1', true);
            xhr.send();
            return false;
        }
        </script>
        """
        while curr < last:
            r += \
                '<a href="{url}"{extra} '\
                'onclick="return update_schedule(\'{url}\', event)">{title}</a>' \
                .format(
                    title = curr.strftime(self.time_format),
                    extra = ' class="selected"' if curr == date else '',
                    url = models.Diffusion.route_url(
                        routes.DateRoute,
                        year = curr.year, month = curr.month, day = curr.day,
                    )
                )
            curr += tz.timedelta(days=1)
        return r



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
