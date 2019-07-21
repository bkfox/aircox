from django.utils.html import format_html, mark_safe
from content_editor.renderer import PluginRenderer

from .models import *


site_renderer = PluginRenderer()
site_renderer._renderers.clear()
site_renderer.register(SiteRichText, lambda plugin: mark_safe(plugin.text))
site_renderer.register(SiteImage, lambda plugin: plugin.render())
site_renderer.register(SiteLink, lambda plugin: plugin.render())


page_renderer = PluginRenderer()
page_renderer._renderers.clear()
page_renderer.register(ArticleRichText, lambda plugin: mark_safe(plugin.text))
page_renderer.register(ArticleImage, lambda plugin: plugin.render())

