from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver

from programs.models import *


class Thread (models.Model):
    post_type = models.ForeignKey(ContentType)
    post_id = models.PositiveIntegerField()
    post = GenericForeignKey('post_type', 'post_id')

    @classmethod
    def get (cl, model, **kwargs):
        post_type = ContentType.objects.get_for_model(model)
        return cl.objects.get(post_type__pk = post_type.id,
                              **kwargs)

    @classmethod
    def filter (cl, model, **kwargs):
        post_type = ContentType.objects.get_for_model(model)
        return cl.objects.filter(post_type__pk = post_type.id,
                              **kwargs)

    @classmethod
    def exclude (cl, model, **kwargs):
        post_type = ContentType.objects.get_for_model(model)
        return cl.objects.exclude(post_type__pk = post_type.id,
                              **kwargs)

    def __str__ (self):
        return str(self.post)


class Post (models.Model):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.SET_NULL,
        blank = True, null = True,
        help_text = _('the publication is posted on this thread'),
    )
    author = models.ForeignKey(
        User,
        verbose_name = _('author'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default = timezone.datetime.now
    )
    public = models.BooleanField(
        verbose_name = _('public'),
        default = True
    )
    image = models.ImageField(
        blank = True, null = True
    )


    def as_dict (self):
        d = {}
        d.update(self.__dict__)
        d.update({
            'title': self.get_title(),
            'image': self.get_image(),
            'date': self.get_date(),
            'content': self.get_content()
        })

    def get_detail_url (self):
        pass

    def get_image (self):
        return self.image

    def get_date (self):
        return self.date

    def get_title (self):
        pass

    def get_content (self):
        pass

    class Meta:
        abstract = True


@receiver(post_save)
def on_new_post (sender, instance, created, *args, **kwargs):
    """
    Signal handler to create a thread that is attached to the newly post
    """
    if not issubclass(sender, Post) or not created:
        return

    thread = Thread(post = instance)
    thread.save()


class ObjectDescription (Post):
    object_type = models.ForeignKey(ContentType, blank = True, null = True)
    object_id = models.PositiveIntegerField(blank = True, null = True)
    object = GenericForeignKey('object_type', 'object_id')



class Article (Post):
    title = models.CharField(
        _('title'),
        max_length = 128,
    )
    static_page = models.BooleanField(
        _('static page'),
        default = False,
    )
    focus = models.BooleanField(
        _('article is focus'),
        default = False,
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

#class MenuItem ():
#    Menu = {
#        'top':      0x00,
#        'sidebar':  0x01,
#        'bottom':   0x02,
#    }
#    for key, value in Type.items():
#        ugettext_lazy(key)
#
#    parent = models.ForeignKey(
#        'self',
#        blank = True, null = True
#    )
#    menu = models.SmallIntegerField(
#    )


