from django.contrib import admin
from django.urls import path, include, reverse
from django.utils.translation import ugettext_lazy as _

from rest_framework.routers import DefaultRouter

from .models import Program
from .views.admin import StatisticsView


__all__ = ['AdminSite']


class AdminSite(admin.AdminSite):
    extra_urls = None
    tools = [
        (_('Statistics'), 'admin:tools-stats'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = DefaultRouter()
        self.extra_urls = []
        self.tools = type(self).tools.copy()

    def each_context(self, request):
        context = super().each_context(request)
        context.update({
            'programs': Program.objects.all().active().values('pk', 'title') \
                                             .order_by('title'),
        })
        return context

    def get_urls(self):
        urls = super().get_urls() + [
            path('api/', include((self.router.urls, 'api'))),
            path('tools/statistics/',
                 self.admin_view(StatisticsView.as_view()),
                 name='tools-stats'),
            path('tools/statistics/<date:date>/',
                 self.admin_view(StatisticsView.as_view()),
                 name='tools-stats'),
        ] + self.extra_urls
        return urls

    def get_tools(self):
        return [(label, reverse(url)) for label, url in self.tools]

    def route_view(self, url, view, name, admin_view=True, label=None):
        self.extra_urls.append(path(
            url, self.admin_view(view) if admin_view else view, name=name
        ))

        if label:
            self.tools.append((label, 'admin:' + name))


