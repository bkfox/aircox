from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import Category, Article, NavItem


__all__ = ['CategoryAdmin', 'PageAdmin', 'NavItemInline']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'slug']
    list_editable = ['title', 'slug']
    search_fields = ['title']
    fields = ['title', 'slug']
    prepopulated_fields = {"slug": ("title",)}


# limit category choice
class PageAdmin(admin.ModelAdmin):
    list_display = ('cover_thumb', 'title', 'status', 'category')
    list_display_links = ('cover_thumb', 'title')
    list_editable = ('status', 'category')
    list_filter = ('status', 'category')
    prepopulated_fields = {"slug": ("title",)}

    search_fields = ['title', 'category__title']
    fieldsets = [
        ('', {
            'fields': ['title', 'slug', 'category', 'cover', 'content'],
        }),
        (_('Publication Settings'), {
            'fields': ['featured', 'allow_comments', 'status'],
            'classes': ('collapse',),
        }),
    ]

    change_form_template = 'admin/aircox/page_change_form.html'

    def cover_thumb(self, obj):
        return mark_safe('<img src="{}"/>'.format(obj.cover.icons['64'])) \
            if obj.cover else ''


class NavItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NavItem



