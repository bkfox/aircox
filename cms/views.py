from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.utils.translation import ugettext as _, ugettext_lazy
from django.http import Http404

from django.views.decorators.http import require_http_methods

class PostBaseView:
    website = None  # corresponding website
    title = ''      # title of the page
    embed = False   # page is embed (if True, only post content is printed
    classes = ''    # extra classes for the content

    def get_base_context(self, **kwargs):
        """
        Return a context with all attributes of this classe plus 'view' set
        to self.
        """
        context = {
            k: getattr(self, k)
            for k, v in PostBaseView.__dict__.items()
                if not k.startswith('__')
        }

        if not self.embed:
            context['menus'] = {
                k: v.get(self.request, object = self.object, **kwargs)
                for k, v in {
                    k: self.website.get_menu(k)
                    for k in self.website.menu_layouts
                }.items() if v
            }
        context['view'] = self
        return context


class PostListView(PostBaseView, ListView):
    """
    List view for posts and children.

    Request.GET params:
    * embed: view is embedded, render only the list
    * exclude: exclude item of the given id
    * order: 'desc' or 'asc'
    * fields: fields to render
    * page: page number
    """
    template_name = 'aircox/cms/list.html'
    allow_empty = True
    paginate_by = 25
    model = None

    route = None
    fields = [ 'date', 'time', 'image', 'title', 'content' ]
    icon_size = '64x64'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.route = self.kwargs.get('route') or self.route
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.route:
            qs = self.route.get_queryset(self.website, self.model, self.request,
                                         **self.kwargs)
        else:
            qs = self.queryset or self.model.objects.all()

        query = self.request.GET
        if query.get('exclude'):
            qs = qs.exclude(id = int(query['exclude']))

        if query.get('embed'):
            self.embed = True

        if query.get('order') == 'asc':
            qs.order_by('date', 'id')
        else:
            qs.order_by('-date', '-id')

        if query.get('fields'):
            self.fields = [
                field for field in query.get('fields')
                if field in self.__class__.fields
            ]

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context(**kwargs))
        context.update({
            'title': self.get_title(),
        })
        return context

    def get_title(self):
        if self.title:
            return self.title

        title = self.route and self.route.get_title(self.model, self.request,
                                                    **self.kwargs)
        return title

    def get_url(self):
        if self.route:
            return self.model(self.route, self.kwargs)
        return ''


from honeypot.decorators import verify_honeypot_value
from aircox.cms.forms import CommentForm

class PostDetailView(DetailView, PostBaseView):
    """
    Detail view for posts and children

    Request.GET params:
    * embed: view is embedded, only render the content
    """
    template_name = 'aircox/cms/detail.html'

    sections = []

    def __init__(self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = sections or []

    def get_queryset(self):
        if self.request.GET.get('embed'):
            self.embed = True
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
        context.update(self.get_base_context())

        kwargs['object'] = self.object
        context['content'] = ''.join([
            section.get(request = self.request, **kwargs)
            for section in self.sections
        ])
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle new comments
        """
        self.object = self.get_object()
        if not self.object:
            raise Http404()

        comment_form = CommentForm(request.POST)
        if not comment_form.is_valid() or verify_honeypot_value(request, 'hp_website'):
            raise Http404()
        comment = comment_form.save(commit=False)
        comment.thread = self.object
        comment.save()

        return self.get(request, *args, **kwargs)



class Menu(View):
    template_name = 'aircox/cms/content_object.html'
    tag = 'nav'
    classes = ''
    attrs = ''
    name = ''
    enabled = True
    position = ''   # top, left, bottom, right, header, footer, page_top, page_bottom
    sections = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes += ' menu menu_{}'.format(self.name or self.position)
        if not self.attrs:
            self.attrs = {}
        if self.name:
            self.attrs['name'] = self.name
            self.attrs['id'] = self.name

    def get_context_data(self, request, object = None, **kwargs):
        kwargs['object'] = object

        return {
            'tag': self.tag,
            'classes': self.classes,
            'attrs': self.attrs,
            'content': ''.join([
                section.get(request, **kwargs)
                for section in self.sections
            ])
        }

    def get(self, request, object = None, **kwargs):
        self.request = request
        context = self.get_context_data(request, object, **kwargs)
        return render_to_string(self.template_name, context)



