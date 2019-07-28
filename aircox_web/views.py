from collections import OrderedDict, deque
import datetime

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, ContextMixin

from content_editor.contents import contents_for_item

from aircox import models as aircox
from .models import Site, Page, DiffusionPage, ProgramPage, \
        get_diffusions_with_page
from .renderer import site_renderer, page_renderer


def route_page(request, path=None, *args, model=None, site=None, **kwargs):
    """
    Route request to page of the provided path. If model is provided, uses
    it.
    """
    # TODO/FIXME: django site framework | site from request host
    # TODO: extra page kwargs (as in pepr)
    site = Site.objects.all().order_by('-default').first() \
           if site is None else site

    model = model if model is not None else Page
    page = get_object_or_404(
        model.objects.select_subclasses().live(),
        path=path
    )
    kwargs['page'] = page
    return page.view(request, *args, site=site, **kwargs)


class BaseView(TemplateResponseMixin, ContextMixin):
    site = None
    """ Current website """
    nav_side = False
    """ Show side navigation """
    title = None
    """ Page title """
    cover = None
    """ Page cover """

    def dispatch(self, request, *args, site=None, **kwargs):
        self.site = site if site is not None else \
            Site.objects.all().order_by('-default').first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if kwargs.get('site_regions') is None:
            contents = contents_for_item(
                self.site, site_renderer._renderers.keys())
            kwargs['site_regions'] = contents.render_regions(site_renderer)

        kwargs.setdefault('site', self.site)
        kwargs.setdefault('cover', self.cover)
        kwargs.setdefault('nav_side', self.nav_side)
        return super().get_context_data(**kwargs)


class PageView(BaseView, DetailView):
    """ Base view class for pages. """
    template_name = 'aircox_web/page.html'
    context_object_name = 'page'
    page = None

    def get_queryset(self):
        return super().get_queryset().live()

    def get_context_data(self, **kwargs):
        page = getattr(self, 'object', None)
        if page is not None:
            if kwargs.get('regions') is None:
                contents = contents_for_item(
                    page, page_renderer._renderers.keys())
                kwargs['regions'] = contents.render_regions(page_renderer)

            kwargs.setdefault('title', page.title)
            kwargs.setdefault('cover', page.cover)
            kwargs.setdefault('page', page)
        return super().get_context_data(**kwargs)


class BaseProgramView(PageView):
    """ Base view class for programs and their sub-pages. """
    nav_side = True
    list_count=5

    def get_diffusions_queryset(self, program, queryset=None):
        qs = get_diffusions_with_page() if queryset is None else queryset
        return qs.before().filter(program=program).order_by('-start')

    def get_context_data(self, program, **kwargs):
        if not hasattr(program, 'page') or not program.page.is_published:
            raise Http404

        if 'diffusions' not in kwargs:
            diffs = self.get_diffusions_queryset(program)[:self.list_count]
            kwargs['diffusions'] = diffs
        return super().get_context_data(program=program, **kwargs)


class ProgramPageView(BaseProgramView):
    template_name = 'aircox_web/program_page.html'
    model = ProgramPage

    def get_queryset(self):
        return super().get_queryset().select_related('program')

    def get_context_data(self, **kwargs):
        kwargs.setdefault('program', self.object.program)
        return super().get_context_data(**kwargs)


class DiffusionPageView(BaseProgramView):
    template_name = 'aircox_web/program_base.html'
    model = DiffusionPage

    def get_podcasts(self, diffusion):
        return aircox.Sound.objects.diffusion(diffusion).podcasts()

    def get_context_data(self, **kwargs):
        diffusion = self.object.diffusion
        kwargs.setdefault('program', diffusion.program)
        kwargs.setdefault('parent', getattr(kwargs['program'], 'page', None))
        if not 'podcasts' in kwargs:
            kwargs['podcasts'] = self.get_podcasts(diffusion)
            print('get prodcasts...', kwargs['podcasts'], diffusion)
        return super().get_context_data(**kwargs)


# TODO: pagination: in template, only a limited number of pages displayed
# DiffusionsView use diffusion instead of diffusion page for different reasons:
# more straightforward, it handles reruns
class DiffusionsView(BaseView, ListView):
    template_name = 'aircox_web/diffusions.html'
    model = aircox.Diffusion
    paginate_by = 30
    program = None

    def get(self, request, *args, **kwargs):
        program_slug = kwargs.get('program_slug')
        if program_slug:
            self.program = get_object_or_404(
                aircox.Program, slug=kwargs.get('program_slug'))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = get_diffusions_with_page(super().get_queryset()) \
            .select_related('page', 'program')
        if self.program:
            qs = qs.filter(program=self.program)
        return qs.order_by('-start')

    def get_context_data(self, **kwargs):
        program = kwargs.setdefault('program', self.program)
        if program is not None and hasattr(program, 'page'):
            kwargs.setdefault('cover', program.page.cover)
            kwargs.setdefault('parent', program.page)
        return super().get_context_data(**kwargs)


class TimetableView(BaseView, ListView):
    """ View for timetables """
    template_name = 'aircox_web/timetable.html'
    model = aircox.Diffusion

    title = _('Timetable')

    date = None
    start = None
    end = None

    def get_queryset(self):
        self.date = self.kwargs.get('date') or datetime.date.today()
        self.start = self.date - datetime.timedelta(days=self.date.weekday())
        self.end = self.start + datetime.timedelta(days=7)
        return super().get_queryset().station(self.site.station) \
                                     .range(self.start, self.end) \
                                     .order_by('start')

    def get_context_data(self, **kwargs):
        # regoup by dates
        by_date = OrderedDict()
        date = self.start
        while date < self.end:
            by_date[date] = []
            date += datetime.timedelta(days=1)

        for diffusion in self.object_list:
            if not diffusion.date in by_date:
                continue
            by_date[diffusion.date].append(diffusion)

        return super().get_context_data(
            by_date=by_date,
            date=self.date,
            start=self.start,
            end=self.end - datetime.timedelta(days=1),
            prev_date=self.start - datetime.timedelta(days=1),
            next_date=self.end + datetime.timedelta(days=1),
            **kwargs
        )


class LogViewBase(ListView):
    station = None
    date = None
    delta = None

    def get_queryset(self):
        # only get logs for tracks: log for diffusion will be retrieved
        # by the diffusions' queryset.
        return super().get_queryset().station(self.station).on_air() \
                      .at(self.date).filter(track__isnull=False)

    def get_diffusions_queryset(self):
        return aircox.Diffusion.objects.station(self.station).on_air() \
                               .at(self.date)

    def get_object_list(self, queryset):
        diffs = deque(self.get_diffusions_queryset().order_by('start'))
        logs = list(queryset.order_by('date'))
        if not len(diffs):
            return logs

        object_list = []
        diff = diffs.popleft()
        last_collision = None

        # diff.start < log on first diff
        # diff.end > log on last diff

        for index, log in enumerate(logs):
            # get next diff
            if diff.end < log.date:
                diff = diffs.popleft() if len(diffs) else None

            # no more diff that can collide: return list
            if diff is None:
                return object_list + logs[index:]

            # diff colliding with log
            if diff.start <= log.date <= diff.end:
                if object_list[-1] is not diff:
                    object_list.append(diff)
                last_collision = log
            else:
                # add last colliding log: track
                if last_collision is not None:
                    object_list.append(last_collision)

                object_list.append(log)
                last_collision = None
        return object_list


class LogsView(BaseView, LogViewBase):
    """ View for timetables """
    template_name = 'aircox_web/logs.html'
    model = aircox.Log
    title = _('Logs')

    date = None
    max_age = 10

    min_date = None

    def get(self, request, *args, **kwargs):
        self.station = self.site.station

        today = datetime.date.today()
        self.min_date = today - datetime.timedelta(days=self.max_age)
        self.date = min(max(self.min_date, self.kwargs['date']), today) \
            if 'date' in self.kwargs else today
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        today = datetime.date.today()
        max_date = min(max(self.date + datetime.timedelta(days=3),
                           self.min_date + datetime.timedelta(days=6)), today)

        return super().get_context_data(
            date=self.date,
            min_date=self.min_date,
            dates=(date for date in (
                max_date - datetime.timedelta(days=i)
                for i in range(0, 7)) if date >= self.min_date
            ),
            object_list=self.get_object_list(self.object_list),
            **kwargs
        )

