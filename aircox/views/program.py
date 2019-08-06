
from aircox.models import Episode, Program
from .page import PageDetailView


__all__ = ['ProgramPageDetailView', 'ProgramDetailView']


class ProgramPageDetailView(PageDetailView):
    """ Base view class for rendering content of a specific programs. """
    show_side_nav = True
    list_count=5

    def get_episodes_queryset(self, program):
        return program.episode_set.published().order_by('-date')

    def get_context_data(self, program, episodes=None, **kwargs):
        if episodes is None:
            episodes = self.get_episodes_queryset(program)
        return super().get_context_data(
            program=program, episodes=episodes[:self.list_count], **kwargs)


class ProgramDetailView(ProgramPageDetailView):
    model = Program

    def get_context_data(self, **kwargs):
        kwargs.setdefault('program', self.object)
        return super().get_context_data(**kwargs)
