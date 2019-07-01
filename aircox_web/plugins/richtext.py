from django.db import models
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextField


class RichText(models.Model):
    text = RichTextField(_('text'))

    class Meta:
        abstract = True

