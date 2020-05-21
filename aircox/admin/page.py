import urllib

from django.contrib import admin
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import Category, NavItem, Page


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
    list_display = ('cover_thumb', 'title', 'status', 'category', 'parent')
    list_display_links = ('cover_thumb', 'title')
    list_editable = ('status', 'category')
    list_filter = ('status', 'category')
    prepopulated_fields = {"slug": ("title",)}

    # prepopulate fields using changelist's filters
    prepopulated_filters = ('parent',)

    search_fields = ['title', 'category__title']
    fieldsets = [
        ('', {
            'fields': ['title', 'slug', 'category', 'cover', 'content'],
        }),
        (_('Publication Settings'), {
            'fields': ['featured', 'allow_comments', 'status', 'parent'],
            'classes': ('collapse',),
        }),
    ]

    change_form_template = 'admin/aircox/page_change_form.html'

    def cover_thumb(self, obj):
        return mark_safe('<img src="{}"/>'.format(obj.cover.icons['64'])) \
            if obj.cover else ''

    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        filters = QueryDict(request.GET.get('_changelist_filters', ''))
        data['parent'] = filters.get('parent', None)
        return data

    def get_common_context(self, query, extra_context=None):
        extra_context = extra_context or {}
        parent = query.get('parent', None)
        if parent is not None:
            extra_context['parent'] = Page.objects.get(id=parent)
        return extra_context

    def add_view(self, request, form_url='', extra_context=None):
        filters = QueryDict(request.GET.get('_changelist_filters', ''))
        extra_context = self.get_common_context(filters, extra_context)
        return super().add_view(request, form_url, extra_context)

    # TODO: change_view => parent from object

    def changelist_view(self, request, extra_context=None):
        extra_context = self.get_common_context(request.GET, extra_context)
        return super().changelist_view(request, extra_context)


class NavItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NavItem



