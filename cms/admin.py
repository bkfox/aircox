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

admin.site.register(models.Article, PostAdmin)
admin.site.register(models.Comment, CommentAdmin)


