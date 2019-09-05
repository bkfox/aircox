
from django.core.exceptions import FieldDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from ..models import Category
from ..utils import Redirect
from .base import BaseView


__all__ = ['ParentMixin', 'PageDetailView', 'PageListView']


class ParentMixin:
    """
    Optional parent page for a list view. Parent is fetched and passed to the
    template context when `parent_model` is provided (queryset is filtered by
    parent page in such case).
    """
    parent_model = None
    """ Parent model """
    parent_url_kwarg = 'parent_slug'
    """ Url lookup argument """
    parent_field = 'slug'
    """ Parent field for url lookup """
    fk_parent = 'page'
    """ Page foreign key to the parent """
    parent = None
    """ Parent page object """

    def get_parent(self, request, *args, **kwargs):
        if self.parent_model is None or self.parent_url_kwarg not in kwargs:
            return

        lookup = {self.parent_field: kwargs[self.parent_url_kwarg]}
        return get_object_or_404(
            self.parent_model.objects.select_related('cover'), **lookup)

    def get(self, request, *args, **kwargs):
        self.parent = self.get_parent(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.parent is not None:
            lookup = {self.fk_parent: self.parent}
            return super().get_queryset().filter(**lookup)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        parent = kwargs.setdefault('parent', self.parent)
        if parent is not None:
            kwargs.setdefault('cover', parent.cover)
        return super().get_context_data(**kwargs)


# TODO: pagination: in template, only a limited number of pages displayed
class PageListView(BaseView, ListView):
    template_name = 'aircox/page_list.html'
    item_template_name = 'aircox/page_item.html'
    paginate_by = 20
    show_headline = True
    show_side_nav = True
    categories = None

    def get(self, *args, **kwargs):
        self.categories = set(self.request.GET.getlist('categories'))
        return super().get(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().published() \
                    .select_related('cover', 'category')

        # category can be filtered based on request.GET['categories']
        # (by id)
        if self.categories:
            qs = qs.filter(category__slug__in=self.categories)
        return qs.order_by('-date')

    def get_categories_queryset(self):
        # TODO: use generic reverse field lookup
        categories = self.model.objects.published() \
                               .filter(category__isnull=False) \
                               .values_list('category', flat=True)
        return Category.objects.filter(id__in=categories)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('item_template_name', self.item_template_name)
        kwargs.setdefault('filter_categories', self.get_categories_queryset())
        kwargs.setdefault('categories', self.categories)
        kwargs.setdefault('show_headline', self.show_headline)
        return super().get_context_data(**kwargs)


class PageDetailView(BaseView, DetailView):
    """ Base view class for pages. """
    context_object_name = 'page'

    def get_queryset(self):
        return super().get_queryset().select_related('cover', 'category')

    # This should not exists: it allows mapping not published pages
    # or it should be only used for trashed pages.
    def not_published_redirect(self, page):
        """
        When a page is not published, redirect to the returned url instead
        of an HTTP 404 code. """
        return None

    def get_object(self):
        obj = super().get_object()
        if not obj.is_published:
            redirect_url = self.not_published_redirect(obj)
            if redirect_url:
                raise Redirect(redirect_url)
            raise Http404('%s not found' % self.model._meta.verbose_name)
        return obj

    def get_context_data(self, **kwargs):
        page = kwargs.setdefault('page', self.object)
        kwargs.setdefault('title', page.title)
        kwargs.setdefault('cover', page.cover)
        return super().get_context_data(**kwargs)



