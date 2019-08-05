from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import NavItem


class PageAdmin(admin.ModelAdmin):
    list_display = ('cover_thumb', 'title', 'status')
    list_display_links = ('cover_thumb', 'title')
    list_editable = ('status',)
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = [
        ('', {
            'fields': ['title', 'slug', 'cover', 'content'],
        }),
        (_('Publication Settings'), {
            'fields': ['featured', 'allow_comments', 'status'],
            'classes': ('collapse',),
        }),
    ]

    def cover_thumb(self, obj):
        return mark_safe('<img src="{}"/>'.format(obj.cover.icons['64'])) \
            if obj.cover else ''


class NavItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NavItem

