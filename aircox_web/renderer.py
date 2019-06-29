from django.utils.html import format_html, mark_safe
from feincms3.renderer import TemplatePluginRenderer

from .models import Page, RichText, Image


renderer = TemplatePluginRenderer()
renderer.register_string_renderer(
    RichText,
    lambda plugin: mark_safe(plugin.text),
)
renderer.register_string_renderer(
    Image,
    lambda plugin: format_html(
        '<figure><img src="{}" alt=""/><figcaption>{}</figcaption></figure>',
        plugin.image.url,
        plugin.caption,
    ),
)

