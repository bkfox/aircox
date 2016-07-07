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
        Similar to View.as_view, but instead, wrap a constructor of the
        given class that is used as is.
        """
        def func(**kwargs_):
            if kwargs_:
                kwargs.update(kwargs_)
            instance = cl(*args, **kwargs)
            return instance
        return func

    @classmethod
    def extends (cl, **kwargs):
        """
        Return a sub class where the given attribute have been updated
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

        for i, section in enumerate(self):
            if callable(section) or type(section) == type:
                self[i] = section()

    def render(self, *args, **kwargs):
        return ''.join([
            section.render(*args, **kwargs)
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

    Attributes:
    * template_name: template to use for rendering
    * tag: container's tags
    * name: set name/id of the section container
    * css_class: css classes of the container
    * attr: HTML attributes of the container
    * title: title of the section
    * header: header of the section
    * footer: footer of the section
    """
    template_name = 'aircox/cms/website.html'

    tag = 'div'
    name = ''
    css_class = ''
    attrs = None
    title = ''
    header = ''
    footer = ''

    request = None
    object = None
    kwargs = None

    def add_css_class(self, css_class):
        if self.css_class:
            if css_class not in self.css_class.split(' '):
                self.css_class += ' ' + css_class
        else:
            self.css_class = css_class

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_css_class('section')
        if type(self) != Section:
            self.add_css_class('section_' + type(self).__name__.lower())

        if not self.attrs:
            self.attrs = {}
        if self.name:
            self.attrs['name'] = self.name
            self.attrs['id'] = self.name

    def get_content(self):
        return ''

    def get_context_data(self, request = None, object = None, **kwargs):
        if request: self.request = request
        if object: self.object = object
        if kwargs: self.kwargs = kwargs

        return {
            'view': self,
            'exp': (hasattr(self, '_exposure') and self._exposure) or None,
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'title': self.title,
            'header': self.header,
            'footer': self.footer,
            'content': self.get_content(),
            'object': self.object,
            'embed': True,
        }

    def render(self, request, object=None, context_only=False, **kwargs):
        context = self.get_context_data(request=request, object=object, **kwargs)
        if context_only:
            return context
        if not context:
            return ''
        context['embed'] = True
        return render_to_string(self.template_name, context, request=request)


class Image(Section):
    """
    Render an image using the relative url or relative to self.object.

    Attributes:
    * url: relative image url
    * rel_attr: name of the attribute of self.object to use
    """
    url = None
    rel_attr = 'image'

    def get_content(self, **kwargs):
        if self.url is None:
            image = getattr(self.object, self.rel_attr)
            return '<img src="{}">'.format(image.url) if image else ''
        return '<img src="{}">'.format(static(self.url))


class Content(Section):
    """
    Render content using the self.content or relative to self.object.

    Attributes:
    * content: raw HTML code to render
    * rel_attr: name of the attribute of self.object to use
    * re_image_attr: if true and there is an image on the current object,
      render the object's image
    """
    content = None
    rel_attr = 'content'
    rel_image_attr = 'image'

    def get_content(self):
        if self.content is None:
            content = getattr(self.object, self.rel_attr)
            content = escape(content)
            content = re.sub(r'(^|\n\n)((\n?[^\n])+)', r'<p>\2</p>', content)
            content = re.sub(r'\n', r'<br>', content)

            if self.rel_image_attr and hasattr(self.object, self.rel_image_attr):
                image = getattr(self.object, self.rel_image_attr)
                if image:
                    content = '<img src="{}">'.format(image.url) + content
            return content
        return str(self.content)


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
            self.url = post.url()


class List(Section):
    """
    Common interface for list configuration.

    Attributes:
    * object_list: force an object list to be used
    * url: url to the list in full page
    * message_empty: message to print when list is empty (if not hiding)
    * fields: fields of the items to render
    * image_size: size of the images
    * truncate: number of words to keep in content (0 = full content)
    """
    template_name = 'aircox/cms/list.html'

    object_list = None
    url = None
    message_empty = _('nothing')
    paginate_by = 4

    fields = [ 'date', 'time', 'image', 'title', 'content', 'info', 'actions' ]
    image_size = '64x64'
    truncate = 16

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

    def get_object_list(self):
        return self.object_list

    def prepare_list(self, object_list):
        """
        Prepare objects before context is sent to the template renderer.
        Return the object_list that is prepared.
        """
        return object_list

    def get_context_data(self, request, object=None, object_list=None,
                            *args, **kwargs):
        """
        Return a context that is passed to the template at rendering, with
        the following values:
        - `list`: a reference to self, that contain values used for rendering
        - `object_list`: a list of object that can be rendered, either
            instances of Post or ListItem.

        If object_list is not given, call `get_object_list` to retrieve it.
        Prepare the object_list using `self.prepare_list`.

        Set `request`, `object`, `object_list` and `kwargs` in self.
        """
        if request: self.request = request
        if object: self.object = object
        if kwargs: self.kwargs = kwargs

        if object_list is None:
            object_list = self.object_list or self.get_object_list()
            if not object_list and not self.message_empty:
                return

        self.object_list = object_list
        if object_list:
            object_list = self.prepare_list(object_list)
            Actions.make(request, object_list = object_list)

        context = super().get_context_data(request, object, *args, **kwargs)
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
    message_empty = _('no comment yet')

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

    def get_context_data(self, *args, **kwargs):
        super().get_context_data(*args, **kwargs)
        return {
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'content': self.sections.render(*args, **kwargs)
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

    def get_content(self):
        import aircox.cms.routes as routes
        url = self.model.reverse(routes.SearchRoute)
        return """
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
        context.update({
            'first_weekday': first,
            'days': [
                (date + tz.timedelta(days=day), self.model.reverse(
                        routes.DateRoute, year = date.year, month = date.month,
                        day = day
                    )
                ) for day in range(0, count)
            ],

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



