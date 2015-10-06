from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse

from django.db.models.signals import post_init, post_save, post_delete
from django.dispatch import receiver

from taggit.managers import TaggableManager


class Post (models.Model):
    thread_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank = True, null = True
    )
    thread_pk = models.PositiveIntegerField(
        blank = True, null = True
    )
    thread = GenericForeignKey('thread_type', 'thread_pk')

    author = models.ForeignKey(
        User,
        verbose_name = _('author'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default = timezone.datetime.now
    )
    published = models.BooleanField(
        verbose_name = _('public'),
        default = True
    )

    title = models.CharField (
        _('title'),
        max_length = 128,
    )
    content = models.TextField (
        _('description'),
        blank = True, null = True
    )
    image = models.ImageField(
        blank = True, null = True
    )
    tags = TaggableManager(
        _('tags'),
        blank = True,
    )

    def detail_url (self):
        return reverse(self._meta.verbose_name.lower() + '_detail',
                       kwargs = { 'pk': self.pk,
                                  'slug': slugify(self.title) })

    class Meta:
        abstract = True


class Article (Post):
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

        if not '__str__' in attrs:
            attrs['__str__'] = lambda self: str(self.related)

        if name is not 'RelatedPost':
            _relation = RelatedPost.Relation()
            _relation.__dict__.update(rel)
            attrs['_relation'] = _relation

        return super().__new__(cls, name, bases, attrs)


class RelatedPost (Post, metaclass = RelatedPostBase):
    related = None

    class Meta:
        abstract = True

    class Relation:
        related_model = None
        mapping = None          # dict of related mapping values
        bind_mapping = False    # update fields of related data on save

    def get_attribute (self, attr):
        attr = self._relation.mappings.get(attr)
        return self.related.__dict__[attr] if attr else None

    def save (self, *args, **kwargs):
        if not self.title and self.related:
            self.title = self.get_attribute('title')

        if self._relation.bind_mapping:
            self.related.__dict__.update({
                rel_attr: self.__dict__[attr]
                for attr, rel_attr in self.Relation.mapping.items()
            })
            self.related.save()

        super().save(*args, **kwargs)


