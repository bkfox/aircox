from ..models import Article, Program, StaticPage
from .page import PageDetailView, PageListView


__all__ = ['ArticleDetailView', 'ArticleListView']


class ArticleDetailView(PageDetailView):
    has_sidebar = True
    model = Article

    def get_sidebar_queryset(self):
        qs = Article.objects.published().select_related('cover') \
                    .order_by('-pub_date')
        return qs


class ArticleListView(PageListView):
    model = Article
    has_headline = True
    parent_model = Program
    attach_to_value = StaticPage.ATTACH_TO_ARTICLES


