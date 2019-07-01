from django.db import models
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, mark_safe

from easy_thumbnails.files import get_thumbnailer
from filer.fields.image import FilerImageField

__all__ = ['ImageBase', 'Image']


class ImageBase(models.Model):
    image = FilerImageField(
        on_delete=models.CASCADE,
        verbose_name=_('image'),
    )
    width = None
    height = None
    crop = False

    class Meta:
        abstract = True

    @property
    def thumbnail(self):
        if self.width == None and self.height == None:
            return self.image
        opts = {}
        if self.crop:
            opts['crop'] = 'smart'
        opts['size'] = (self.width or 0, self.height or 0)
        thumbnailer = get_thumbnailer(self.image)
        return thumbnailer.get_thumbnail(opts)

    def render(self):
        return format_html('<img src="{}" alt=""/>', self.thumbnail.url)


class Image(ImageBase):
    width = models.PositiveSmallIntegerField(blank=True,null=True)
    height = models.PositiveSmallIntegerField(blank=True,null=True)
    crop = models.BooleanField(default=False)

    class Meta:
        abstract = True


