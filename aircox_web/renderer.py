from django.utils.html import format_html, mark_safe
from feincms3.renderer import TemplatePluginRenderer

from .models import *


site_renderer = TemplatePluginRenderer()
site_renderer.register_string_renderer(
    SiteRichText,
    lambda plugin: mark_safe(plugin.text),
)
site_renderer.register_string_renderer(
    SiteImage,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)


page_renderer = TemplatePluginRenderer()
page_renderer.register_string_renderer(
    PageRichText,
    lambda plugin: mark_safe(plugin.text),
)
page_renderer.register_string_renderer(
    PageImage,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)

