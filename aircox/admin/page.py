from copy import deepcopy

from django.contrib import admin
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import Category, NavItem, Page, StaticPage


__all__ = ['CategoryAdmin', 'PageAdmin', 'NavItemInline']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'slug']
    list_editable = ['title', 'slug']
    search_fields = ['title']
    fields = ['title', 'slug']
    prepopulated_fields = {"slug": ("title",)}


class BasePageAdmin(admin.ModelAdmin):
    list_display = ('cover_thumb', 'title', 'status', 'parent')
    list_display_links = ('cover_thumb', 'title')
    list_editable = ('status',)
    list_filter = ('status',)
    prepopulated_fields = {"slug": ("title",)}

    # prepopulate fields using changelist's filters
    prepopulated_filters = ('parent',)

    search_fields = ('title',)
    fieldsets = [
        ('', {
            'fields': ['title', 'slug', 'cover', 'content'],
        }),
        (_('Publication Settings'), {
            'fields': ['status', 'parent'],
            # 'classes': ('collapse',),
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
        extra_context['parent'] = None if parent is None else \
                                  Page.objects.get_subclass(id=parent)

        return extra_context

    def render_change_form(self, request, context, *args, **kwargs):
        if context['original'] and not 'parent' in context:
            context['parent'] = context['original'].parent
        return super().render_change_form(request, context, *args, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        filters = QueryDict(request.GET.get('_changelist_filters', ''))
        extra_context = self.get_common_context(filters, extra_context)
        return super().add_view(request, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = self.get_common_context(request.GET, extra_context)
        return super().changelist_view(request, extra_context)


class PageAdmin(BasePageAdmin):
    change_list_template = 'admin/aircox/page_change_list.html'

    list_display = BasePageAdmin.list_display + ('category',)
    list_editable = BasePageAdmin.list_editable + ('category',)
    list_filter = BasePageAdmin.list_editable + ('category',)
    search_fields = ('category__title',)
    fieldsets = deepcopy(BasePageAdmin.fieldsets)

    fieldsets[0][1]['fields'].insert(fieldsets[0][1]['fields'].index('slug') + 1, 'category')
    fieldsets[1][1]['fields'] += ('featured', 'allow_comments')


@admin.register(StaticPage)
class StaticPageAdmin(BasePageAdmin):
    list_display = BasePageAdmin.list_display + ('attach_to',)
    fieldsets = deepcopy(BasePageAdmin.fieldsets)

    fieldsets[1][1]['fields'] += ('attach_to',)


class NavItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NavItem

