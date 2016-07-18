"""
Define different Section css_class that can be used by views.Sections;
"""
import re
import datetime # used in calendar
from random import shuffle

from django.utils import timezone as tz
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.templatetags.static import static
from django.http import HttpResponse
from django.contrib import messages
from django.utils.html import escape
from django.utils.translation import ugettext as _, ugettext_lazy

from honeypot.decorators import check_honeypot

from aircox.cms.forms import CommentForm
from aircox.cms.exposures import expose
from aircox.cms.actions import Actions


class Viewable:
    """
    Describe a view that is still usable as a class after as_view() has
    been called.
    """
    @classmethod
    def as_view (cl, *args, **kwargs):
        """
        Create a view containing the current viewable, using a subclass
        of aircox.cms.views.BaseView.
        All the arguments are passed to the view directly.
        """
        from aircox.cms.views import PageView
        kwargs['sections'] = cl
        return PageView.as_view(*args, **kwargs)

    @classmethod
    def extends (cl, **kwargs):
        """
        Return a sub class where the given attribute have been updated
        using kwargs.
        """
        class Sub(cl):
            pass
        Sub.__name__ = cl.__name__

        for k, v in kwargs.items():
            setattr(Sub, k, v)

        if hasattr(cl, '_exposure'):
            return expose(Sub)
        return Sub


class Sections(Viewable, list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        """
        prepare all children sections
        """
        for i, section in enumerate(self):
            if callable(section) or type(section) == type:
                self[i] = section()
            self[i].prepare(*args, **kwargs)

    def render(self, *args, **kwargs):
        if args:
            self.prepare(*args, **kwargs)
        return ''.join([
            section.render()
            for section in self
        ])

    def filter(self, predicate):
        return [ section for section in self if predicate(section) ]


class Section(Viewable, View):
    """
    On the contrary to Django's views, we create an instance of the view
    only once, when the server is run.

    Attributes are not changed once they have been set, and are related
    to Section configuration/rendering. However, some data are considered
    as temporary, and are reset at each rendering, using given arguments.

    When get_context_data returns None, returns an empty string

    ! Important Note: values given for rendering are considered as safe
    HTML in templates.
    """
    template_name = 'aircox/cms/website.html'
    """
    Template used for rendering
    """
    tag = 'div'
    """
    HTML tag used for the container
    """
    name = ''
    """
    Name/ID of the container
    """
    css_class = ''
    """
    CSS classes for the container
    """
    attrs = None
    """
    HTML Attributes of the container
    """
    title = ''
    """
    Safe HTML code for the title
    """
    header = ''
    """
    Safe HTML code for the header
    """
    footer = ''
    """
    Safe HTML code for the footer
    """
    message_empty = None
    """
    If message_empty is not None, print its value as
    content of the section instead of hiding it. This works also when
    its value is an empty string (prints an empty string).
    """

    view = None
    request = None
    object = None
    kwargs = None

    def add_css_class(self, css_class):
        if self.css_class:
            if css_class not in self.css_class.split(' '):
                self.css_class += ' ' + css_class
        else:
            self.css_class = css_class

    def __init__ (self, **kwargs):
        super().__init__(**kwargs)

        self.add_css_class('section')
        if type(self) != Section:
            self.add_css_class('section_' + type(self).__name__.lower())

        if not self.attrs:
            self.attrs = {}
        if self.name:
            self.attrs['name'] = self.name
            self.attrs['id'] = self.name

    def is_empty(self):
        """
        Return True if the section content will be empty. This allows to
        hide the section.
        This must be implemented by the subclasses.
        """
        return False

    def get_context_data(self):
        return {
            'view': self,
            'exp': (hasattr(self, '_exposure') and self._exposure) or None,
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'title': self.title,
            'header': self.header,
            'footer': self.footer,
            'content': '',
            'object': self.object,
            'embed': True,
        }

    def prepare(self, view, **kwargs):
        """
        initialize the object with valuable informations.
        """
        self.view = view
        self.request = view.request
        self.kwargs = view.kwargs
        if hasattr(view, 'object'):
            self.object = view.object

    def render(self, *args, **kwargs):
        """
        Render the section as a string. Use *args and **kwargs to prepare
        the section, then get_context_data and render.
        """
        if args and not self.view:
            self.prepare(*args, **kwargs)
        context = self.get_context_data()

        is_empty = self.is_empty()
        if not context or (is_empty and not self.message_empty):
            return ''

        if is_empty and self.message_empty:
            context['content'] = self.message_empty

        context['embed'] = True
        return render_to_string(
            self.template_name, context, request=self.request
        )


class Image(Section):
    """
    Render an image using the relative url or relative to self.object.

    Attributes:
    * url: relative image url
    * img_attr: name of the attribute of self.object to use
    """
    url = None
    img_attr = 'image'

    def get_image(self):
        if self.url:
            return static(self.url)
        if hasattr(self.object, self.img_attr):
            image = getattr(self.object, self.img_attr)
            return (image and image.url) or None

    def is_empty(self):
        return not self.get_image()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        url = self.get_image()
        if url:
            context['content'] += '<img src="{}">'.format(url)
        return context

class Content(Image):
    """
    Render content using the self.content or relative to self.object.
    Since it is a child of Image, can also render an image.

    Attributes:
    * content: raw HTML code to render
    * content_attr: name of the attribute of self.object to use
    """
    # FIXME: markup language -- coordinate with object's one (post/comment)?
    content = None
    content_attr = 'content'

    def get_content(self):
        if self.content:
            return self.content
        if hasattr(self.object, self.content_attr):
            return getattr(self.object, self.content_attr) or None

    def is_empty(self):
        return super().is_empty() and not self.get_content()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        content = self.get_content()
        if content:
            if not self.content:
                content = escape(content)
                content = re.sub(r'(^|\n\n)((\n?[^\n])+)', r'<p>\2</p>', content)
                content = re.sub(r'\n', r'<br>', content)

            context['content'] += content
        return context


class ListItem:
    """
    Used to render items in simple lists and lists of posts.

    In list of posts, it is used when an object is not a post but
    behaves like it.
    """
    title = None
    content = None
    author = None
    date = None
    image = None
    info = None
    url = None
    actions = None

    css_class = None
    attrs = None

    def __init__ (self, post = None, **kwargs):
        if post:
            self.update(post)
        self.__dict__.update(**kwargs)

    def update(self, post):
        """
        Update empty fields using the given post
        """
        for i in self.__class__.__dict__.keys():
            if i[0] == '_':
                continue
            if hasattr(post, i) and not getattr(self, i):
                setattr(self, i, getattr(post, i))
        if not self.url and hasattr(post, 'url'):
            self.url = post.url() if callable(post.url) else post.url


class List(Section):
    """
    Common interface for list configuration.

    Attributes:
    """
    template_name = 'aircox/cms/list.html'

    object_list = None
    """
    Use this object list (default behaviour for lists)
    """
    url = None
    """
    URL to the list in full page; If given, print it
    """
    paginate_by = 4

    fields = [ 'date', 'time', 'image', 'title', 'content', 'info', 'actions' ]
    """
    Fields that must be rendered.
    """
    image_size = '64x64'
    """
    Size of the image when rendered in the list
    """
    truncate = 16
    """
    Number of words to print in content. If 0, print all the content
    """

    def __init__ (self, items = None, *args, **kwargs):
        """
        If posts is given, create the object_list with instances
        of ListItem.
        """
        super().__init__(*args, **kwargs)
        self.add_css_class('list')

        if items:
            self.object_list = [
                ListItem(item) for item in items
            ]

    @classmethod
    def as_view(cl, *args, **kwargs):
        from aircox.cms.views import PostListView
        kwargs['sections'] = cl
        return PostListView.as_view(*args, **kwargs)

    def is_empty(self):
        return not self.object_list

    def get_object_list(self):
        return self.object_list or []

    def prepare_list(self, object_list):
        """
        Prepare objects before context is sent to the template renderer.
        Return the object_list that is prepared.
        """
        return object_list

    def get_context_data(self, *args, object_list=None, **kwargs):
        """
        Return a context that is passed to the template at rendering, with
        the following values:
        - `list`: a reference to self, that contain values used for rendering
        - `object_list`: a list of object that can be rendered, either
            instances of Post or ListItem.

        If object_list is not given, call `get_object_list` to retrieve it.
        Prepare the object_list using `self.prepare_list`, and make actions
        for its items.

        Set `request`, `object`, `object_list` and `kwargs` in self.
        """
        if args:
            self.prepare(*args, **kwargs)

        if object_list is None:
            object_list = self.object_list or self.get_object_list()
            if not object_list and not self.message_empty:
                return {}

        self.object_list = object_list
        if object_list:
            object_list = self.prepare_list(object_list)
            Actions.make(self.request, object_list = object_list)

        context = super().get_context_data()
        context.update({
            'list': self,
            'object_list': object_list[:self.paginate_by]
                           if object_list and self.paginate_by else
                           object_list,
        })
        return context

    def need_url(self):
        """
        Return True if there should be a pagination url
        """
        return self.paginate_by and self.paginate_by < len(self.object_list)


class Similar(List):
    """
    Section that uses tags to render similar objects of a given one.
    Note that the list is not a queryset, but the sorted result of
    taggit's similar_objects function.
    """
    title = _('Similar publications')
    models = None
    """
    List of models allowed in the resulting list. If not set, all models
    are available.
    """
    shuffle = 20
    """
    Shuffle results in the self.shuffle most recents articles. If 0 or
    None, do not shuffle.
    """

    # FIXME: limit in a date range
    def get_object_list(self):
        if not self.object:
            return

        qs = self.object.tags.similar_objects()
        qs.sort(key = lambda post: post.date, reverse=True)
        if self.shuffle:
            qs = qs[:self.shuffle]
            shuffle(qs)
        return qs


class Comments(List):
    """
    Section used to render comment form and comments list. It renders the
    form and comments, and save them.
    """
    template_name = 'aircox/cms/comments.html'
    title=_('Comments')
    css_class='comments'
    truncate = 0
    fields = [ 'date', 'time', 'author', 'content' ]
    message_empty = _('no comment has been posted yet')

    comment_form = None
    success_message = ( _('Your message is awaiting for approval'),
                        _('Your message has been published') )
    error_message = _('There was an error while saving your post. '
                      'Please check errors below')

    def get_object_list(self):
        if not self.object:
            return
        qs = self.object.get_comments().filter(published=True). \
                         order_by('-date')
        return [ ListItem(post=comment, css_class="comment",
                          attrs={ 'id': comment.id })
                 for comment in qs ]

    @property
    def url(self):
        import aircox.cms.models as models
        import aircox.cms.routes as routes
        if self.object:
            return models.Comment.reverse(routes.ThreadRoute, {
                'pk': self.object.id,
                'thread_model': self.object._registration.name
            })
        return ''

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        comment_form = None
        if self.object:
            post = self.object
            if hasattr(post, 'allow_comments') and post.allow_comments:
                comment_form = (self.comment_form or CommentForm())

        context.update({
            'comment_form': comment_form,
        })
        self.comment_form = None
        return context

    def post(self, view, request, object):
        """
        Forward data to this view
        """
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.thread = object
            comment.published = view.website.auto_publish_comments
            comment.save()

            messages.success(request, self.success_message[comment.published],
                             fail_silently=True)
        else:
            messages.error(request, self.error_message, fail_silently=True)
        self.comment_form = comment_form


class Menu(Section):
    tag = 'nav'
    position = ''   # top, left, bottom, right, header, footer, page_top, page_bottom
    sections = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('menu')
        self.add_css_class('menu_' + str(self.name or self.position))
        self.sections = Sections(self.sections)

        if not self.attrs:
            self.attrs = {}

    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)
        self.sections.prepare(*args, **kwargs)

    def get_context_data(self):
        return {
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'content': self.sections.render()
        }


class Search(Section):
    """
    Implement a search form that can be used in menus. Model must be set,
    even if it is a generic model, in order to be able to reverse urls.
    """
    model = None
    """
    Model to search on
    """
    placeholder = _('Search %(name_plural)s')
    """
    Placeholder in the input text. The string is formatted before rendering.
    - name: model's verbose name
    - name_plural: model's verbose name in plural form
    """
    no_button = True
    """
    Hide submit button if true
    """
    # TODO: (later) autocomplete using exposures -> might need templates

    def get_context_data(self, *args, **kwargs):
        import aircox.cms.routes as routes
        context = super().get_context_data(*args, **kwargs)
        url = self.model.reverse(routes.SearchRoute)

        context['content'] += """
        <form action="{url}" method="get">
            <input type="text" name="q" placeholder="{placeholder}"/>
            <input type="submit" {submit_style}/>
        </form>
        """.format(
            url = url, placeholder = self.placeholder % {
                'name': self.model._meta.verbose_name,
                'name_plural': self.model._meta.verbose_name_plural,
            },
            submit_style = (self.no_button and 'style="display: none;"') or '',
        )
        return context


@expose
class Calendar(Section):
    model = None
    template_name = "aircox/cms/calendar.html"

    def get_context_data(self, year = None, month = None, *args, **kwargs):
        import calendar
        import aircox.cms.routes as routes
        context = super().get_context_data(*args, **kwargs)

        date = datetime.date.today()
        if year:
            date = date.replace(year = year)
        if month:
            date = date.replace(month = month)
        date = date.replace(day = 1)

        first, count = calendar.monthrange(date.year, date.month)
        def make_date(date, day):
            date += tz.timedelta(days=day)
            return (
                date, self.model.reverse(
                    routes.DateRoute, year = date.year,
                    month = date.month, day = date.day
                )
            )

        context.update({
            'first_weekday': first,
            'days': [ make_date(date, day) for day in range(0, count) ],
            'today': datetime.date.today(),
            'this_month': date,
            'prev_month': date - tz.timedelta(days=10),
            'next_month': date + tz.timedelta(days=count),
        })
        return context

    @expose
    def render_exp(cl, *args, year, month, **kwargs):
        year = int(year)
        month = int(month)
        return cl.render(*args, year = year, month = month, **kwargs)

    render_exp._exposure.name = 'render'
    render_exp._exposure.pattern = '(?P<year>[0-9]{4})/(?P<month>[0-1]?[0-9])'



