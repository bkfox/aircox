from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic.base import TemplateView

from content_editor.contents import contents_for_item

from .models import Site, Page
from .renderer import site_renderer, page_renderer


def route_page(request, path=None, *args, site=None, **kwargs):
    # TODO/FIXME: django site framework | site from request host
    # TODO: extra page kwargs (as in pepr)
    site = Site.objects.all().order_by('-default').first() \
           if site is None else site
    page = get_object_or_404(
        # TODO: published
        Page.objects.select_subclasses()
                    .filter(Q(status=Page.STATUS.published) |
                            Q(status=Page.STATUS.announced)),
        path="/{}/".format(path) if path else "/",
    )
    kwargs['page'] = page
    return page.view(request, *args, site=site, **kwargs)


class PageView(TemplateView):
    """ Base view class for pages. """
    template_name = 'aircox_web/page.html'

    site = None
    page = None

    def get_context_data(self, **kwargs):
        page = kwargs.setdefault('page', self.page or self.kwargs.get('site'))
        site = kwargs.setdefault('site', self.site or self.kwargs.get('site'))

        if kwargs.get('regions') is None:
            contents = contents_for_item(page, page_renderer._renderers.keys())
            kwargs['regions'] = contents.render_regions(page_renderer)

        if kwargs.get('site_regions') is None:
            contents = contents_for_item(site, site_renderer._renderers.keys())
            kwargs['site_regions'] = contents.render_regions(site_renderer)
        return super().get_context_data(**kwargs)



