from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ..models import Episode, Program, Page, StaticPage
from .mixins import ParentMixin, AttachedToMixin
from .page import PageDetailView, PageListView


__all__ = ['ProgramPageDetailView', 'ProgramDetailView', 'ProgramPageListView']


class BaseProgramMixin:
    def get_program(self):
        return self.object

    def get_sidebar_url(self):
        return reverse('program-page-list',
                       kwargs={"parent_slug": self.program.slug})

    def get_context_data(self, **kwargs):
        self.program = self.get_program()
        kwargs['program'] = self.program
        return super().get_context_data(**kwargs)


class ProgramDetailView(BaseProgramMixin, PageDetailView):
    model = Program

    def get_sidebar_queryset(self):
        return super().get_sidebar_queryset().filter(parent=self.program)


class ProgramListView(PageListView):
    model = Program
    attach_to_value = StaticPage.ATTACH_TO_PROGRAMS


# FIXME: not used
class ProgramPageDetailView(BaseProgramMixin, ParentMixin, PageDetailView):
    """
    Base view class for a page that is displayed as a program's child page.
    """
    parent_model = Program

    def get_program(self):
        self.parent = self.object.program
        return self.object.program

    def get_sidebar_queryset(self):
        return super().get_sidebar_queryset().filter(parent=self.program)


class ProgramPageListView(BaseProgramMixin, PageListView):
    model = Page
    parent_model = Program
    queryset = Page.objects.select_subclasses()

    def get_program(self):
        return self.parent

    def get_context_data(self, **kwargs):
        kwargs.setdefault('sidebar_url_parent', None)
        return super().get_context_data(**kwargs)

