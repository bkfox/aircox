from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse

from django.db.models.signals import Signal, post_save
from django.dispatch import receiver

import bleach
from taggit.managers import TaggableManager

from aircox.cms import routes
from aircox.cms import settings


class Routable:
    @classmethod
    def get_with_thread(cl, thread = None, queryset = None,
                        thread_model = None, thread_id = None):
        """
        Return posts of the cl's type that are children of the given thread.
        """
        if not queryset:
            queryset = cl.objects

        if thread:
            thread_model = type(thread)
            thread_id = thread.id

        thread_model = ContentType.objects.get_for_model(thread_model)
        return queryset.filter(
            thread_id = thread_id,
            thread_type__pk = thread_model.id
        )

    @classmethod
    def route_url(cl, route, **kwargs):
        name = cl._website.name_of_model(cl)
        name = route.get_view_name(name)
        r = reverse(name, kwargs = kwargs)
        return r


class Comment(models.Model, Routable):
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
        default = False
    )

    author = models.CharField(
        verbose_name = _('author'),
        max_length = 32,
    )
    email = models.EmailField(
        verbose_name = _('email'),
        blank = True, null = True,
    )
    url = models.URLField(
        verbose_name = _('website'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default = timezone.datetime.now
    )
    content = models.TextField (
        _('comment'),
    )

    def make_safe(self):
        self.author = bleach.clean(self.author, tags=[])
        if self.email:
            self.email = bleach.clean(self.email, tags=[])
        if self.url:
            self.url = bleach.clean(self.url, tags=[])
        self.content = bleach.clean(
            self.content,
            tags=settings.AIRCOX_CMS_BLEACH_COMMENT_TAGS,
            attributes=settings.AIRCOX_CMS_BLEACH_COMMENT_ATTRS
        )

    def save(self, make_safe = True, *args, **kwargs):
        if make_safe:
            self.make_safe()
        return super().save(*args, **kwargs)


class Post (models.Model, Routable):
    """
    Base model that can be used as is if wanted. Represent a generic
    publication on the website.

    You can declare an extra property "info" that can be used to append
    info in lists rendering.
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
        default = '',
    )
    image = models.ImageField(
        blank = True, null = True,
    )
    tags = TaggableManager(
        verbose_name = _('tags'),
        blank = True,
    )

    search_fields = [ 'title', 'content' ]

    def get_comments(self):
        """
        Return comments pointing to this post
        """
        type = ContentType.objects.get_for_model(self)
        qs = Comment.objects.filter(
            thread_id = self.pk,
            thread_type__pk = type.pk
        )
        return qs

    def url(self):
        """
        Return an url to the post detail view.
        """
        return self.route_url(
            routes.DetailRoute,
            pk = self.pk, slug = slugify(self.title)
        )

    def get_object_list(self, request, object, **kwargs):
        type = ContentType.objects.get_for_model(object)
        qs = Comment.objects.filter(
            thread_id = object.pk,
            thread_type__pk = type.pk
        )
        return qs

    def make_safe(self):
        self.title = bleach.clean(
            self.title,
            tags=settings.AIRCOX_CMS_BLEACH_TITLE_TAGS,
            attributes=settings.AIRCOX_CMS_BLEACH_TITLE_ATTRS
        )
        self.content = bleach.clean(
            self.content,
            tags=settings.AIRCOX_CMS_BLEACH_CONTENT_TAGS,
            attributes=settings.AIRCOX_CMS_BLEACH_CONTENT_ATTRS
        )
        if self.pk:
            self.tags.set(*[
                bleach.clean(tag, tags=[])
                for tag in self.tags.all()
            ])

    def save(self, make_safe = True, *args, **kwargs):
        if make_safe:
            self.make_safe()
        if self.date and self.date.tzinfo is None or \
                self.date.tzinfo.utcoffset(self.date) is None:
            timezone.make_aware(self.date)
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


class RelatedMeta (models.base.ModelBase):
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

    @classmethod
    def make_auto_create(cl, model):
        if not model._relation.rel_to_post:
            return

        def handler(sender, instance, created, *args, **kwargs):
            rel = model._relation
            post = model.objects.filter(related = instance)
            if post.count():
                post = post[0]
            elif rel.auto_create(instance) if callable(rel.auto_create) else \
                 rel.auto_create:
                post = model(related = instance)
            else:
                return
            post.rel_to_post()
            post.save(avoid_sync = True)
        post_save.connect(handler, model._relation.model, False)

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
        cl.register(rel.model, model)

        # auto create and/or update
        cl.make_auto_create(model)

        # name clashes
        name = rel.model._meta.object_name
        if name == model._meta.object_name:
            model._meta.default_related_name = '{} Post'.format(name)

        return model


class RelatedPost (Post, metaclass = RelatedMeta):
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

    # FIXME: declare a binding only for init
    class Relation:
        """
        Relation descriptor used to generate and manage the related object.

        Be careful with post_to_rel!
        * There is no check of permissions when related object is synchronised
            from the post, so be careful when enabling post_to_rel.
        * In post_to_rel synchronisation, if the parent thread is not a
            (sub-)class thread_model, the related parent is set to None
        """
        model = None
        """
        model of the related object
        """
        bindings = None
        """
        dict of `post_attr: rel_attr` that represent bindings of values
        between the post and the related object. Field are updated according
        to `post_to_rel` and `rel_to_post`.

        If there is a post_attr "thread", the corresponding rel_attr is used
        to update the post thread to the correct Post model (in order to
        establish a parent-child relation between two models)

        When a callable is set as `rel_attr`, it will be called to retrieve
        the value, as `rel_attr(post, related)`

        note: bound values can be any value, not only Django field.
        """
        post_to_rel = False
        """
        update related object when the post is saved, using bindings
        """
        rel_to_post = False
        """
        update the post when related object is updated, using bindings
        """
        thread_model = None
        """
        generated by the metaclass, points to the RelatedPost model
        generated for the bindings.thread object.
        """
        field_args = None
        """
        dict of arguments to pass to the ForeignKey constructor, such as
        `ForeignKey(related_model, **field_args)`
        """
        auto_create = False
        """
        automatically create a RelatedPost for each new item of the related
        object and init it with bounded values. Use 'post_save' signal. If
        auto_create is callable, use `auto_create(related_object)`.
        """

    def get_rel_attr(self, attr):
        attr = self._relation.bindings.get(attr)
        if callable(attr):
            return attr(self, self.related)
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
        if not self.related or not rel.bindings:
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
        if not self.related or not rel.bindings:
            return

        has_changed = False
        def set_attr(attr, value):
            if getattr(self, attr) != value:
                has_changed = True
                setattr(self, attr, value)

        for attr, rel_attr in rel.bindings.items():
            if attr == 'thread':
                continue
            value = rel_attr(self, self.related) if callable(rel_attr) else \
                    getattr(self.related, rel_attr)
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
            self.rel_to_post(False)

    def save (self, avoid_sync = False, save = True, *args, **kwargs):
        """
        * avoid_sync: do not synchronise the post/related object;
        * save: if False, does not call parent save functions
        """
        if not avoid_sync:
            if not self.pk and self._relation.rel_to_post:
                self.rel_to_post(False)
            if self._relation.post_to_rel:
                self.post_to_rel(True)
        if save:
            super().save(*args, **kwargs)

