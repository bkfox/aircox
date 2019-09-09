from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from ..models import Episode, Program, Page
from .mixins import ParentMixin
from .page import PageDetailView, PageListView


__all__ = ['ProgramPageDetailView', 'ProgramDetailView', 'ProgramPageListView']


class ProgramPageDetailView(PageDetailView):
    """
    Base view class for a page that is displayed as a program's child page.
    """
    program = None
    has_sidebar = True
    list_count = 5

    def get_sidebar_queryset(self):
        return super().get_sidebar_queryset().filter(parent=self.object)


class ProgramPageListView(ParentMixin, PageListView):
    model = Page
    parent_model = Program
    queryset = Page.objects.select_subclasses()


class ProgramDetailView(ProgramPageDetailView):
    model = Program

    def get_context_data(self, **kwargs):
        self.program = kwargs.setdefault('program', self.object)
        return super().get_context_data(**kwargs)



