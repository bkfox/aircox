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

from aircox.cms import routes


class ProxyPost:
    """
    Class used to simulate a Post model when it is required to render an
    item linked to a Post but that is not that itself. This is to ensure
    the right attributes are set.
    """
    detail_url = None
    date = None
    image = None
    title = None
    content = None

    def __init__(self, post = None, **kwargs):
        if post:
            self.update_empty(post)
        self.__dict__.update(**kwargs)

    def update_empty(self, thread):
        """
        Update empty fields using thread object
        """
        for i in ('date', 'image', 'title', 'content'):
            if not getattr(self, i):
                setattr(self, i, getattr(thread, i))
        if not self.detail_url:
            self.detail_url = thread.detail_url()


class Post (models.Model):
    """
    Base model that can be used as is if wanted. Represent a generic
    publication on the website.
    """
    # metadata
    thread_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank = True, null = True
    )
    thread_id = models.PositiveIntegerField(
        blank = True, null = True
    )
    thread = GenericForeignKey('thread_type', 'thread_id')

    published = models.BooleanField(
        verbose_name = _('public'),
        default = True
    )
    allow_comments = models.BooleanField(
        verbose_name = _('allow comments'),
        default = True,
    )

    # content
    author = models.ForeignKey(
        User,
        verbose_name = _('author'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default = timezone.datetime.now
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

    search_fields = [ 'title', 'content' ]

    def get_proxy(self):
        """
        Return a ProxyPost instance using this post
        """
        return ProxyPost(self)

    @classmethod
    def children_of(cl, thread, queryset = None):
        """
        Return children of the given thread of the cl's type. If queryset
        is not given, use cl.objects as starting queryset.
        """
        if not queryset:
            queryset = cl.objects
        thread_type = ContentType.objects.get_for_model(thread)
        qs = queryset.filter(thread_id = thread.pk,
                              thread_type__pk = thread_type.id)
        return qs

    def detail_url(self):
        return self.route_url(routes.DetailRoute,
                              { 'pk': self.pk, 'slug': slugify(self.title) })

    @classmethod
    def route_url(cl, route, kwargs = None):
        name = cl._website.name_of_model(cl)
        name = route.get_view_name(name)
        return reverse(name, kwargs = kwargs)

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
    def register (cl, key, post_model):
        """
        Register a model and return the key under which it is registered.
        Raise a ValueError if another model is yet associated under this key.
        """
        if key in cl.registry and cl.registry[key] is not post_model:
            raise ValueError('A model has yet been registered with "{}"'
                             .format(key))
        cl.registry[key] = post_model
        return key

    @classmethod
    def make_relation(cl, name, attrs):
        """
        Make instance of RelatedPost.Relation
        """
        rel = RelatedPost.Relation()
        if 'Relation' not in attrs:
            raise ValueError('RelatedPost item has not defined Relation class')
        rel.__dict__.update(attrs['Relation'].__dict__)

        if not rel.model or not issubclass(rel.model, models.Model):
            raise ValueError('Relation.model is not a django model (None?)')

        if not rel.bindings:
            rel.bindings = {}

        # thread model
        if rel.bindings.get('thread'):
            rel.thread_model = rel.bindings.get('thread')
            rel.thread_model = rel.model._meta.get_field(rel.thread_model). \
                               rel.to
            rel.thread_model = cl.registry.get(rel.thread_model)

            if not rel.thread_model:
                raise ValueError(
                    'no registered RelatedPost for the bound thread. Is there '
                    ' a RelatedPost for {} declared before {}?'
                    .format(rel.bindings.get('thread').__class__.__name__,
                            name)
                )

        return rel

    def __new__ (cl, name, bases, attrs):
        # TODO: allow proxy models and better inheritance
        # TODO: check bindings
        if name == 'RelatedPost':
            return super().__new__(cl, name, bases, attrs)

        rel = cl.make_relation(name, attrs)
        field_args = rel.field_args or {}
        attrs['_relation'] = rel
        attrs.update({ x:y for x,y in {
            'related': models.ForeignKey(rel.model, **field_args),
            '__str__': lambda self: str(self.related)
        }.items() if not attrs.get(x) })

        model = super().__new__(cl, name, bases, attrs)
        print(model, model.related)
        cl.register(rel.model, model)

        # name clashes
        name = rel.model._meta.object_name
        if name == model._meta.object_name:
            model._meta.default_related_name = '{} Post'.format(name)

        return model


class RelatedPost (Post, metaclass = RelatedPostBase):
    """
    Post linked to an object of other model. This object is accessible through
    the field "related".

    It is possible to map attributes of the Post to the ones of the Related
    Object. It is also possible to automatically update Post's thread based
    on the Related Object's parent if it is required (but not Related Object's
    parent based on Post's thread).

    Bindings can ensure that the Related Object will be updated when mapped
    fields of the Post are updated.

    To configure the Related Post, you just need to create set attributes of
    the Relation sub-class.

    ```
    class MyModelPost(RelatedPost):
        class Relation:
            model = MyModel
            bindings = {
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
        * bindings: values that are bound between the post and the related
            object. When the post is saved, these fields are updated on it.
            It is a dict of { post_attr: rel_attr }

            If there is a post_attr "thread", the corresponding rel_attr is used
            to update the post thread to the correct Post model (in order to
            establish a parent-child relation between two models)

            Note: bound values can be any value, not only Django field.
        * post_to_rel: auto update related object when post is updated
        * rel_to_post: auto update the post when related object is updated
        * thread_model: generated by the metaclass, points to the RelatedPost
            model generated for the bindings.thread object.
        * field_args: dict of arguments to pass to the ForeignKey constructor,
            such as: ForeignKey(related_model, **field_args)

        Be careful with post_to_rel!
        * There is no check of permissions when related object is synchronised
            from the post, so be careful when enabling post_to_rel.
        * In post_to_rel synchronisation, if the parent thread is not a
            (sub-)class thread_model, the related parent is set to None
        """
        model = None
        bindings = None          # values to map { post_attr: rel_attr }
        post_to_rel = False
        rel_to_post = False
        thread_model = None
        field_args = None

    def get_rel_attr(self, attr):
        attr = self._relation.bindings.get(attr)
        return getattr(self.related, attr) if attr else None

    def set_rel_attr(self, attr, value):
        if attr not in self._relation.bindings:
            raise AttributeError('attribute {} is not bound'.format(attr))
        attr = self._relation.bindings.get(attr)
        setattr(self.related, attr, value)

    def post_to_rel(self, save = True):
        """
        Change related object using post bound values. Save the related
        object if save = True.
        Note: does not check if Relation.post_to_rel is True
        """
        rel = self._relation
        if not rel.bindings:
            return

        for attr, rel_attr in rel.bindings.items():
            if attr == 'thread':
                continue
            value = getattr(self, attr) if hasattr(self, attr) else None
            setattr(self.related, rel_attr, value)

        if rel.thread_model:
            thread = self.thread if not issubclass(thread, rel.thread_model) \
                        else None
            self.set_rel_attr('thread', thread.related)

        if save:
            self.related.save()


    def rel_to_post(self, save = True):
        """
        Change the post using the related object bound values. Save the
        post if save = True.
        Note: does not check if Relation.post_to_rel is True
        """
        rel = self._relation
        if not rel.bindings:
            return

        has_changed = False
        def set_attr(attr, value):
            if getattr(self, attr) != value:
                has_changed = True
                setattr(self, attr, value)

        for attr, rel_attr in rel.bindings.items():
            if attr == 'thread':
                continue
            self.set_rel_attr
            value = getattr(self.related, rel_attr)
            set_attr(attr, value)

        if rel.thread_model:
            thread = self.get_rel_attr('thread')
            thread = rel.thread_model.objects.filter(related = thread) \
                        if thread else None
            thread = thread[0] if thread else None
            set_attr('thread', thread)

        if has_changed and save:
            self.save()

    def __init__ (self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)
        # we use this method for sync, in order to avoid intrusive code on other
        # applications, e.g. using signals.
        if self.pk and self._relation.rel_to_post:
            self.rel_to_post(save = False)

    def save (self, *args, **kwargs):
        # TODO handle when related change
        if not self.title and self.related:
            self.title = self.get_rel_attr('title')
        if self._relation.post_to_rel:
            self.post_to_rel(save = True)
        super().save(*args, **kwargs)


class Comment(models.Model):
    thread_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank = True, null = True
    )
    thread_id = models.PositiveIntegerField(
        blank = True, null = True
    )
    thread = GenericForeignKey('thread_type', 'thread_id')

    author = models.TextField(
        verbose_name = _('author'),
        blank = True, null = True,
    )
    email = models.EmailField(
        verbose_name = _('email'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default = timezone.datetime.now
    )
    content = models.TextField (
        _('description'),
        blank = True, null = True
    )



