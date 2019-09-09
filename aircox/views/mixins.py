import dateutil
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ..utils import str_to_date


__all__ = ['GetDateMixin', 'ParentMixin']


class GetDateMixin:
    """
    Mixin offering utils to get date by `request.GET` or
    `kwargs['date']`
    """
    date = None
    redirect_date_url = None

    def get_date(self):
        date = self.request.GET.get('date')
        return str_to_date(date, '-') if date is not None else \
            self.kwargs['date'] if 'date' in self.kwargs else None

    def get(self, *args, **kwargs):
        if self.redirect_date_url and self.request.GET.get('date'):
            return redirect(self.redirect_date_url,
                            date=self.request.GET['date'].replace('-', '/'))

        self.date = self.get_date()
        return super().get(*args, **kwargs)


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
            return super().get_queryset().filter(parent=self.parent)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        parent = kwargs.setdefault('parent', self.parent)
        if parent is not None:
            kwargs.setdefault('cover', parent.cover)
        return super().get_context_data(**kwargs)


