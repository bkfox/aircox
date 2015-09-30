from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver

import programs.models as programs


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


class BasePost (models.Model):
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

    title = ''
    content = ''

    class Meta:
        abstract = True


@receiver(post_save)
def on_new_post (sender, instance, created, *args, **kwargs):
    """
    Signal handler to create a thread that is attached to the newly post
    """
    if not issubclass(sender, BasePost) or not created:
        return

    thread = Thread(post = instance)
    thread.save()


class Post (BasePost):
    class Meta:
        abstract = True

    @staticmethod
    def create_related_post (model, maps):
        """
        Create a subclass of BasePost model, that binds the common-fields
        using the given maps. The maps' keys are the property to change, and
        its value is the target model's attribute (or a callable)
        """
        class Meta:
            pass

        attrs = {
            '__module__': BasePost.__module__,
            'Meta': Meta,
            'related': models.ForeignKey(model),
            '__str__': lambda self: str(self.related)
        }

        def get_prop (name, related_name):
            return property(related_name) if callable(related_name) \
                    else property(lambda self: getattr(self.related, related_name))

        attrs.update({
            name: get_prop(name, related_name)
                for name, related_name in maps.items()
        })
        return type(model.__name__ + 'Post', (BasePost,), attrs)


class Article (BasePost):
    title = models.CharField(
        _('title'),
        max_length = 128,
        blank = False, null = False
    )
    content = models.TextField(
        _('content'),
        blank = False, null = False
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


ProgramPost = Post.create_related_post(programs.Program, {
                    'title': 'name',
                    'content': 'description',
               })


EpisodePost = Post.create_related_post(programs.Episode, {
                    'title': 'name',
                    'content': 'description',
               })



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


