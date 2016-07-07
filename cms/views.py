from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.views.generic.base import View, TemplateView
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib import messages
from django.http import Http404

from aircox.cms.actions import Actions
import aircox.cms.sections as sections
sections_ = sections # used for name clashes


class BaseView:
    """
    Render a page using given sections.

    If sections is a list of sections, then render like a detail view;
    If it is a single section, render it as website.html view;

    # Request GET params:
    * embed: view is embedded, render only the content of the view
    """
    template_name = ''
    """it is set to "aircox/cms/detail.html" to render multiple sections"""
    sections = None
    """sections used to render the page"""
    website = None
    """website that uses the view"""
    menus = None
    """menus used to render the view page"""
    title = ''
    """title of the page (used in <title> tags and page <h1>)"""
    attrs = ''      # attr for the HTML element of the content
    """attributes to set in the HTML element containing the view"""
    css_class = ''  # css classes for the HTML element of the content
    """css classes used for the HTML element containing the view"""

    def __init__(self, sections = None, *args, **kwargs):
        if hasattr(sections, '__iter__'):
            self.sections = sections_.Sections(sections)
        else:
            self.sections = sections
        super().__init__(*args, **kwargs)

    def __section_is_single(self):
        return not issubclass(type(self.sections), list)

    def add_css_class(self, css_class):
        """
        Add the given class to the current class list if not yet present.
        """
        if self.css_class:
            if css_class not in self.css_class.split(' '):
                self.css_class += ' ' + css_class
        else:
            self.css_class = css_class

    def get_context_data(self, **kwargs):
        """
        Return a context with all attributes of this classe plus 'view' set
        to self.
        """
        context = {}

        # update from sections
        if self.sections:
            if self.__section_is_single():
                self.template_name = self.sections.template_name
                context.update(self.sections.get_context_data(
                    self.request,
                    object_list = hasattr(self, 'object_list') and \
                                    self.object_list,
                    **self.kwargs
                ) or {})
            else:
                if not self.template_name:
                    self.template_name = 'aircox/cms/detail.html'
                context.update({
                    'content': self.sections.render(self.request, **kwargs)
                })

        context.update(super().get_context_data(**kwargs))

        # then from me
        context.update({
            'website': self.website,
            'view': self,
            'title': self.title,
            'tag': 'main',
            'attrs': self.attrs,
            'css_class': self.css_class,
        })

        if 'embed' not in self.request.GET:
            if not kwargs.get('object'):
                kwargs['object'] = self.object if hasattr(self, 'object') \
                                    else None
            if self.menus:
                context['menus'] = {
                    k: v.render(self.request, **kwargs)
                    for k, v in self.menus.items()
                    if v is not self
                }
            context['actions'] = Actions.register_code()
            context['embed'] = False
        else:
            context['embed'] = True
        return context


class PostListView(BaseView, ListView):
    """
    List view for posts and children.

    If list is given:
    - use list's template and css_class
    - use list's context as base context

    Note that we never use list.get_object_list, but instead use
    route.get_queryset or self.model.objects.all()

    Request.GET params:
    * exclude: exclude item of the given id
    * order: 'desc' or 'asc'
    * page: page number
    """
    template_name = 'aircox/cms/list.html'
    allow_empty = True
    paginate_by = 30
    model = None

    route = None
    """route used to render this list"""

    @property
    def list(self):
        """list section to use to render the list and get base context.
        By default it is sections.List"""
        return self.sections

    @list.setter
    def list(self, value):
        self.sections = value

    def dispatch(self, request, *args, **kwargs):
        self.route = self.kwargs.get('route') or self.route
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.route:
            qs = self.route.get_queryset(self.model, self.request,
                                         **self.kwargs)
        else:
            qs = self.queryset or self.model.objects.all()
        qs = qs.filter(published = True)

        query = self.request.GET
        if query.get('exclude'):
            qs = qs.exclude(id = int(query['exclude']))
        if query.get('order') == 'desc':
            qs = qs.order_by('-date', '-id')
        else:
            qs = qs.order_by('date', 'id')

        return qs

    def prepare_list(self):
        if not self.list:
           self.list = sections.List(
               truncate = 32,
               paginate_by = 0,
           )
        else:
            self.list = self.list(paginate_by = 0)
            self.template_name = self.list.template_name
            self.css_class = self.list.css_class

        if self.request.GET.get('fields'):
            self.list.fields = [
                field for field in self.request.GET.getlist('fields')
                if field in self.list.fields
            ]

        # done in list
        # Actions.make(self.request, object_list = self.object_list)

    def get_context_data(self, **kwargs):
        self.prepare_list()
        self.add_css_class('list')

        context = super().get_context_data(**kwargs)

        if self.route and not context.get('title'):
            context['title'] = self.route.get_title(
                self.model, self.request, **self.kwargs
            )

        context['list'] = self.list
        return context


class PostDetailView(BaseView, DetailView):
    """
    Detail view for posts and children
    """
    comments = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('detail')

    def get_queryset(self):
        if self.model:
            return super().get_queryset().filter(published = True)
        return []

    def get_object(self, **kwargs):
        if self.model:
            object = super().get_object(**kwargs)
            if object.published:
                return object
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not context.get('title'):
            context['title'] = self.object.title
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle new comments
        """
        if not self.comments:
            for section in self.sections:
                if issubclass(type(section), sections.Comments):
                    self.comments = section

        self.object = self.get_object()
        self.comments.post(self, request, self.object)
        return self.get(request, *args, **kwargs)


class PageView(BaseView, TemplateView):
    """
    Render a page using given sections.

    If sections is a list of sections, then render like a detail view;
    If it is a single section, render it as website.html view;
    """

