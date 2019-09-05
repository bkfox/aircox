"""
Aircox admin tools and views.
"""
import datetime

from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin, \
        PermissionRequiredMixin, UserPassesTestMixin
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from ..models import Program
from .log import BaseLogListView


class BaseAdminView(LoginRequiredMixin, UserPassesTestMixin):
    title = ''

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        kwargs.update(admin.site.each_context(self.request))
        kwargs.setdefault('title', self.title)
        return super().get_context_data(**kwargs)


class StatisticsView(BaseAdminView, BaseLogListView, ListView):
    template_name = 'admin/aircox/statistics.html'
    title = _('Statistics')
    date = None

    def get_queryset(self):
        return super().get_queryset().today(self.date)

    def get_diffusions_queryset(self):
        return super().get_diffusions_queryset().today(self.date)

    def get(self, request, *args, date=None, **kwargs):
        self.date = datetime.date.today() if date is None else date
        return super().get(request, *args, date=date, **kwargs)


class AdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context.update({
            'programs': Program.objects.all().active().values('pk', 'title'),
        })
        return context

    def get_urls(self):
        from django.urls import path, include
        urls = super().get_urls()
        urls += [
            path('tools/statistics/',
                 self.admin_view(StatisticsView.as_view()),
                 name='tools-stats'),
        ]
        return urls


admin_site = AdminSite()

