from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from .log import LogListView


__all__ = ['BaseAdminView', 'StatisticsView']


class BaseAdminView(LoginRequiredMixin, UserPassesTestMixin):
    title = ''

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        kwargs.update(admin.site.each_context(self.request))
        kwargs.setdefault('title', self.title)
        return super().get_context_data(**kwargs)


class StatisticsView(BaseAdminView, LogListView, ListView):
    template_name = 'admin/aircox/statistics.html'
    redirect_date_url = 'tools-stats'
    title = _('Statistics')
    date = None

    def get_object_list(self, logs, *_):
        return super().get_object_list(logs, True)


