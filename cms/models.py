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
    """
    Base model that can be used as is if wanted. Represent a generic
    publication on the website.
    """
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
    """
    Represent an article or a static page on the website.
    """
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
    registry = {}

    @classmethod
    def register (cl, key, model):
        """
        Register a model and return the key under which it is registered.
        Raise a ValueError if another model is yet associated under this key.
        """
        if key in cl.registry and cl.registry[key] is not model:
            raise ValueError('A model has yet been registered with "{}"'
                             .format(key))
        cl.registry[key] = model
        return key

    @classmethod
    def check_thread_mapping (cl, relation, model, field):
        """
        Add information related to the mapping 'thread' info.
        """
        if not field:
            return

        parent_model = model._meta.get_field(field).rel.to
        thread_model = cl.registry.get(parent_model)

        if not thread_model:
            raise ValueError('no registered RelatedPost for the model {}'
                             .format(model.__name__))
        relation.thread_model = thread_model

    def __new__ (cl, name, bases, attrs):
        rel = attrs.get('Relation')
        rel = (rel and rel.__dict__) or {}

        related_model = rel.get('model')
        if related_model:
            attrs['related'] = models.ForeignKey(related_model)

        if not '__str__' in attrs:
            attrs['__str__'] = lambda self: str(self.related)

        if name is not 'RelatedPost':
            _relation = RelatedPost.Relation()
            _relation.__dict__.update(rel)
            mapping = rel.get('mapping')
            cl.check_thread_mapping(
                _relation,
                related_model,
                mapping and mapping.get('thread')
            )
            attrs['_relation'] = _relation

        model = super().__new__(cl, name, bases, attrs)
        cl.register(related_model, model)
        return model


class RelatedPost (Post, metaclass = RelatedPostBase):
    """
    Post linked to an object of other model. This object is accessible through
    the field "related".

    It is possible to map attributes of the Post to the ones of the Related
    Object. It is also possible to automatically update post's thread based
    on the Related Object's parent if it is required.

    Mapping can ensure that the Related Object will be updated when mapped
    fields of the Post are updated.

    To configure the Related Post, you just need to create set attributes of
    the Relation sub-class.

    ```
    class MyModelPost(RelatedPost):
        class Relation:
            model = MyModel
            mapping = {
                'thread': 'parent_field_name',
                'title': 'name'
            }
    ```
    """
    related = None

    class Meta:
        abstract = True

    class Relation:
        """
        Relation descriptor used to generate and manage the related object.

        * model: model of the related object
        * mapping: values that are bound between the post and the related
            object. When the post is saved, these fields are updated on it.
            It is a dict of { post_attr: rel_attr }

            If there is a post_attr "thread", the corresponding rel_attr is used
            to update the post thread to the correct Post model (in order to
            establish a parent-child relation between two models)
        * thread_model: generated by the metaclass, points to the RelatedPost
            model generated for the mapping.thread object.
        """
        model = None
        mapping = None          # values to map { post_attr: rel_attr }
        thread_model = None

    def get_attribute (self, attr):
        attr = self._relation.mappings.get(attr)
        return self.related.__dict__[attr] if attr else None

    def update_thread_mapping (self, save = True):
        """
        Update the parent object designed by Relation.mapping.thread if the
        type matches to the one related of the current instance's thread.

        If there is no thread assigned to self, set it to the parent of the
        related object.
        """
        relation = self._relation
        thread_model = relation.thread_model
        if not thread_model:
            return

        # self.related.parent -> self.thread
        rel_parent = relation.mapping.get('thread')
        if not self.thread:
            rel_parent = getattr(self.related, rel_parent)
            thread = thread_model.objects.filter(related = rel_parent)
            if thread.count():
                self.thread = thread[0]
                if save:
                    self.save()
            return

        # self.thread -> self.related.parent
        if thread_model is not self.thread_type.model_class():
            return

        setattr(self.related, rel_parent, self.thread.related)
        if save:
            self.save()

    def update_mapping (self):
        relation = self._relation
        mapping = relation.mapping
        if not mapping:
            return

        related = self.related
        related.__dict__.update({
            rel_attr: self.__dict__[attr]
            for attr, rel_attr in mapping.items()
            if attr is not 'thread' and attr in self.__dict__
        })

        self.update_thread_mapping(save = False)
        related.save()

    def save (self, *args, **kwargs):
        if not self.title and self.related:
            self.title = self.get_attribute('title')

        self.update_mapping()
        super().save(*args, **kwargs)


