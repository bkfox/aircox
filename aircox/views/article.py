from ..models import Article, Program
from .mixins import ParentMixin
from .page import PageDetailView, PageListView


__all__ = ['ArticleDetailView', 'ArticleListView']


class ArticleDetailView(PageDetailView):
    show_side_nav = True
    model = Article

    def get_side_queryset(self):
        qs = Article.objects.select_related('cover') \
                    .filter(is_static=False) \
                    .order_by('-date')
        return qs

    def get_context_data(self, **kwargs):
        if self.object.program is not None:
            kwargs.setdefault('parent', self.object.program)
        return super().get_context_data(**kwargs)


class ArticleListView(ParentMixin, PageListView):
    model = Article
    template_name = 'aircox/article_list.html'
    show_headline = True
    is_static = False

    parent_model = Program
    fk_parent = 'program'

    def get_queryset(self):
        return super().get_queryset().filter(is_static=self.is_static)


