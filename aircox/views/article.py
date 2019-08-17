from ..models import Article
from .program import ProgramPageListView


__all__ = ['ArticleListView']


class ArticleListView(ProgramPageListView):
    model = Article
    template_name = 'aircox/article_list.html'
    show_headline = True
    is_static = False

    def get_queryset(self):
        return super().get_queryset(is_static=self.is_static)

