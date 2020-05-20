import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from filer.fields.image import FilerImageField

from .. import settings


__all__ = ['Station', 'StationQuerySet']


class StationQuerySet(models.QuerySet):
    def default(self, station=None):
        """
        Return station model instance, using defaults or
        given one.
        """
        if station is None:
            return self.order_by('-default', 'pk').first()
        return self.filter(pk=station).first()

    def active(self):
        return self.filter(active=True)


class Station(models.Model):
    """
    Represents a radio station, to which multiple programs are attached
    and that is used as the top object for everything.

    A Station holds controllers for the audio stream generation too.
    Theses are set up when needed (at the first access to these elements)
    then cached.
    """
    name = models.CharField(_('name'), max_length=64)
    slug = models.SlugField(_('slug'), max_length=64, unique=True)
    # FIXME: remove - should be decided only by Streamer controller + settings
    path = models.CharField(
        _('path'),
        help_text=_('path to the working directory'),
        max_length=256,
        blank=True,
    )
    default = models.BooleanField(
        _('default station'),
        default=True,
        help_text=_('use this station as the main one.')
    )
    active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('whether this station is still active or not.')
    )
    logo = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Logo'),
    )
    hosts = models.TextField(
        _("website's urls"), max_length=512, null=True, blank=True,
        help_text=_('specify one url per line')
    )
    audio_streams = models.TextField(
        _("audio streams"), max_length=2048, null=True, blank=True,
        help_text=_("Audio streams urls used by station's player. One url "
                    "a line.")
    )

    objects = StationQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, make_sources=True, *args, **kwargs):
        if not self.path:
            self.path = os.path.join(settings.AIRCOX_CONTROLLERS_WORKING_DIR,
                                     self.slug.replace('-', '_'))

        if self.default:
            qs = Station.objects.filter(default=True)
            if self.pk is not None:
                qs = qs.exclude(pk=self.pk)
            qs.update(default=False)

        super().save(*args, **kwargs)


