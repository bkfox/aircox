from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from aircox.models import Episode, Program
from .page import PageDetailView, PageListView


__all__ = ['ProgramPageDetailView', 'ProgramDetailView']


class ProgramPageDetailView(PageDetailView):
    """
    Base view class for a page that is displayed as a program's child page.
    """
    show_side_nav = True
    list_count = 5

    def get_episodes_queryset(self, program):
        return program.episode_set.published().order_by('-date')

    def get_context_data(self, program, episodes=None, **kwargs):
        if episodes is None:
            episodes = self.get_episodes_queryset(program)
        return super().get_context_data(
            program=program, episodes=episodes[:self.list_count], **kwargs)


class ProgramPageListView(PageListView):
    """
    Base list view class rendering pages as a program's child page.
    Retrieved program from it slug provided by `kwargs['program_slug']`.

    This view class can be used with or without providing a program.
    """
    program = None

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('program_slug', None)
        if slug is not None:
            self.program = get_object_or_404(
                Program.objects.select_related('cover'), slug=slug)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(program=self.program) \
               if self.program else super().get_queryset()

    def get_context_data(self, **kwargs):
        program = kwargs.setdefault('program', self.program)
        if program is not None:
            kwargs.setdefault('cover', program.cover)
            kwargs.setdefault('parent', program)
        return super().get_context_data(**kwargs)


class ProgramDetailView(ProgramPageDetailView):
    model = Program

    def get_articles_queryset(self, program):
        return program.article_set.published().order_by('-date')

    def get_context_data(self, **kwargs):
        kwargs.setdefault('program', self.object)
        return super().get_context_data(**kwargs)
