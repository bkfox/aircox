from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.cms.models as models


class PostAdmin(admin.ModelAdmin):
    list_display = [ 'title', 'date', 'author', 'published', 'post_tags']
    list_editable = [ 'published' ]
    list_filter = ['date', 'author', 'published']

    def post_tags(self, post):
        tags = []
        for tag in post.tags.all():
            tags.append(str(tag))
        return ', '.join(tags)
    post_tags.short_description = _('tags')

    def post_image(self, post):
        if not post.image:
            return

        from easy_thumbnails.files import get_thumbnailer
        options = {'size': (48, 48), 'crop': True}
        url = get_thumbnailer(post.image).get_thumbnail(options).url
        return u'<img src="{url}">'.format(url=url)
    post_image.short_description = _('image')
    post_image.allow_tags = True


class RelatedPostAdmin(PostAdmin):
    list_display = ['title', 'date', 'published', 'post_tags', 'post_image' ]


class CommentAdmin(admin.ModelAdmin):
    list_display = [ 'date', 'author', 'published', 'content_slice' ]
    list_editable = [ 'published' ]
    list_filter = ['date', 'author', 'published']

    def content_slice(self, post):
        return post.content[:256]
    content_slice.short_description = _('content')


class PostInline(admin.StackedInline):
    extra = 1
    max_num = 1
    verbose_name = _('Post')

    fieldsets = [
        (None, {
            'fields': ['title', 'content', 'image', 'tags']
        }),
        (None, {
            'fields': ['date', 'published', 'author']
        })
    ]


def inject_related_inline(post_model, prepend = False, inline = None):
    """
    Create an inline class and inject it into the related model admin class.
    Clean-up bound attributes.
    """
    class InlineModel(PostInline):
        model = post_model
        verbose_name = _('Related post')

    inline = inline or InlineModel

    # remove bound attributes
    for none, dic in inline.fieldsets:
        if not dic.get('fields'):
            continue
        dic['fields'] = [ v for v in dic['fields']
                            if v not in post_model._relation.bindings.keys() ]

    inject_inline(post_model._meta.get_field('related').rel.to,
                  inline, prepend)

def inject_inline(model, inline, prepend = False):
    registry = admin.site._registry
    if not model in registry:
        return TypeError('{} not in admin registry'.format(model.__name__))

    inlines = list(registry[model].inlines) or []
    if prepend:
        inlines.insert(0, inline)
    else:
        inlines.append(inline)
    registry[model].inlines = inlines


admin.site.register(models.Comment, CommentAdmin)


