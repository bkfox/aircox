
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView

from honeypot.decorators import check_honeypot

from ..forms import CommentForm
from ..models import Category, Comment
from ..utils import Redirect
from .base import BaseView


__all__ = ['PageDetailView', 'PageListView']


# TODO: pagination: in template, only a limited number of pages displayed
class PageListView(BaseView, ListView):
    template_name = 'aircox/page_list.html'
    item_template_name = 'aircox/page_item.html'
    has_sidebar = True
    has_filters = True

    paginate_by = 20
    show_headline = True
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
        return qs.order_by('-pub_date')

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
    has_filters = False

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
        if getattr(self, 'object', None):
            return self.object

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

        if self.object.allow_comments and not 'comment_form' in kwargs:
            kwargs['comment_form'] = CommentForm()

        kwargs['comments'] = Comment.objects.filter(page=self.object) \
                                            .order_by('-date')
        return super().get_context_data(**kwargs)

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(PageDetailView, cls).as_view(*args, **kwargs)
        return check_honeypot(view, field_name='website')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.allow_comments:
            return HttpResponse(_('comments are not allowed'), status=503)

        form = CommentForm(request.POST)
        comment = form.save(commit=False)
        comment.page = self.object
        comment.save()

        return self.get(request, *args, **kwargs)





