
from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from honeypot.decorators import check_honeypot

from ..forms import CommentForm
from ..models import Category, Comment
from ..utils import Redirect
from .base import BaseView
from .mixins import AttachedToMixin, ParentMixin


__all__ = ['BasePageListView', 'BasePageDetailView', 'PageDetailView', 'PageListView']


class BasePageListView(AttachedToMixin, ParentMixin, BaseView, ListView):
    """ Base view class for BasePage list. """
    template_name = 'aircox/basepage_list.html'
    item_template_name = 'aircox/widgets/page_item.html'
    has_sidebar = True

    paginate_by = 30
    has_headline = True

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses().published() \
                      .select_related('cover')

    def get_context_data(self, **kwargs):
        kwargs.setdefault('item_template_name', self.item_template_name)
        kwargs.setdefault('has_headline', self.has_headline)
        return super().get_context_data(**kwargs)


class BasePageDetailView(BaseView, DetailView):
    """ Base view class for BasePage. """
    template_name = 'aircox/basepage_detail.html'
    context_object_name = 'page'
    has_filters = False

    def get_queryset(self):
        return super().get_queryset().select_related('cover')

    # This should not exists: it allows mapping not published pages
    # or it should be only used for trashed pages.
    def not_published_redirect(self, page):
        """
        When a page is not published, redirect to the returned url instead of an
        HTTP 404 code.
        """
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

    def get_page(self):
        return self.object


class PageListView(BasePageListView):
    """ Page list view. """
    template_name = None
    has_filters = True
    categories = None
    filters = None

    def get(self, *args, **kwargs):
        self.categories = set(self.request.GET.getlist('categories'))
        self.filters = set(self.request.GET.getlist('filters'))
        return super().get(*args, **kwargs)

    def get_template_names(self):
        return super().get_template_names() + ['aircox/page_list.html']

    def get_queryset(self):
        qs = super().get_queryset().select_related('category') \
                                   .order_by('-pub_date')

        # category can be filtered based on request.GET['categories']
        # (by id)
        if self.categories:
            qs = qs.filter(category__slug__in=self.categories)
        return qs

    def get_filters(self):
        categories = self.model.objects.published() \
                               .filter(category__isnull=False) \
                               .values_list('category', flat=True)
        categories = [ (c.title, c.slug, c.slug in self.categories)
                        for c in Category.objects.filter(id__in=categories) ]
        return (
            (_('Categories'), 'categories', categories),
        )

    def get_context_data(self, **kwargs):
        if not 'filters' in kwargs:
            filters = self.get_filters()
            for label, fieldName, choices in filters:
                if choices:
                    kwargs['filters'] = filters
                    break;
            else:
                kwargs['filters'] = tuple()
        return super().get_context_data(**kwargs)


class PageDetailView(BasePageDetailView):
    """ Base view class for pages. """
    template_name = None
    context_object_name = 'page'
    has_filters = False

    def get_template_names(self):
        return super().get_template_names() + ['aircox/page_detail.html']

    def get_queryset(self):
        return super().get_queryset().select_related('category')

    def get_context_data(self, **kwargs):
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

