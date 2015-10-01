from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver


# Using a separate thread helps for routing, by avoiding to specify an
# additional argument to get the second model that implies to find it by
# the name that can be non user-friendly, like /thread/relatedpost/id
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
        return self.post_type.name + ': ' + str(self.post)


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

    title = ''
    content = ''

    def detail_url (self):
        return reverse(self._meta.verbose_name_plural.lower() + '_detail',
                       kwargs = { 'pk': self.pk,
                                  'slug': slugify(self.title) })

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


class Article (Post):
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


class RelatedPostBase (models.base.ModelBase):
    """
    Metaclass for RelatedPost children.
    """
    def __new__ (cls, name, bases, attrs):
        rel = attrs.get('Relation')
        rel = (rel and rel.__dict__) or {}

        related_model = rel.get('related_model')
        if related_model:
            attrs['related'] = models.ForeignKey(related_model)

        mapping = rel.get('mapping')
        if mapping:
            def get_prop (name, related_name):
                return property(related_name) if callable(related_name) \
                        else property(lambda self:
                                        getattr(self.related, related_name))

            attrs.update({
                name: get_prop(name, related_name)
                    for name, related_name in mapping.items()
            })

        if not '__str__' in attrs:
            attrs['__str__'] = lambda self: str(self.related)

        return super().__new__(cls, name, bases, attrs)


class RelatedPost (Post, metaclass = RelatedPostBase):
    class Meta:
        abstract = True

    class Relation:
        related_model = None
        mapping = None


