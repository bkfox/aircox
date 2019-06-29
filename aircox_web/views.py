from django.shortcuts import get_object_or_404, render

from feincms3.regions import Regions

from .models import SiteSettings, Page
from .renderer import renderer


def page_detail(request, path=None):
    page = get_object_or_404(
        # TODO: published
        Page.objects.all(),
        path="/{}/".format(path) if path else "/",
    )
    return render(request, "aircox_web/page.html", {
        'site_settings': SiteSettings.objects.all().first(),
        "page": page,
        "regions": Regions.from_item(
            page, renderer=renderer, timeout=60
        ),
    })

