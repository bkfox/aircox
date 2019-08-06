from ..models import Article
from .page import PageListView


__all__ = ['ArticleListView']


class ArticleListView(PageListView):
    model = Article
    is_static = False

    def get_queryset(self):
        return super().get_queryset(is_static=self.is_static)

