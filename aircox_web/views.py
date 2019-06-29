from django.shortcuts import get_object_or_404, render

from feincms3.regions import Regions

from .models import Site, Page
from .renderer import site_renderer, page_renderer


def page_detail(request, path=None):
    page = get_object_or_404(
        # TODO: published
        Page.objects.all(),
        path="/{}/".format(path) if path else "/",
    )
    site = Site.objects.all().first()
    return render(request, "aircox_web/page.html", {
        'site': site,
        "regions": Regions.from_item(site, renderer=site_renderer, timeout=60),
        "page": page,
        "page_regions": Regions.from_item(page, renderer=page_renderer, timeout=60),
    })

