from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from aircox.models import Episode, Program
from .page import PageDetailView, PageListView


__all__ = ['ProgramPageDetailView', 'ProgramDetailView']


class ProgramPageDetailView(PageDetailView):
    """
    Base view class for a page that is displayed as a program's child page.
    """
    program = None
    show_side_nav = True
    list_count = 5

    def get_side_queryset(self):
        return self.program.episode_set.published().order_by('-date')


class ProgramDetailView(ProgramPageDetailView):
    model = Program

    def get_articles_queryset(self):
        return self.program.article_set.published().order_by('-date')

    def get_context_data(self, **kwargs):
        self.program = kwargs.setdefault('program', self.object)
        if 'articles' not in kwargs:
            kwargs['articles'] = \
                self.get_articles_queryset()[:self.list_count]
        return super().get_context_data(**kwargs)


