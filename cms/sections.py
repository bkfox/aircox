"""
Define different Section css_class that can be used by views.Sections;
"""
import re

from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.contrib import messages
from django.utils.html import escape
from django.utils.translation import ugettext as _, ugettext_lazy

from honeypot.decorators import check_honeypot

from aircox.cms.forms import CommentForm


class Section(View):
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
    * hide_empty: if true, section is not rendered when content is empty

    * title: title of the section
    * header: header of the section
    * footer: footer of the section

    * force_object: (can be persistent) related object

    """
    template_name = 'aircox/cms/section.html'

    tag = 'div'
    name = ''
    css_class = ''
    attrs = None
    # hide_empty = False
    title = ''
    header = ''
    footer = ''
    object = None
    force_object = None

    def add_css_class(self, css_class):
        if self.css_class:
            if css_class not in self.css_class:
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

    def get_context_data(self):
        return {
            'view': self,
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'title': self.title,
            'header': self.header,
            'footer': self.footer,
            'content': self.get_content(),
            'object': self.object,
        }

    def get_context(self, request, object=None, **kwargs):
        self.object = self.force_object or object
        self.request = request
        self.kwargs = kwargs
        return self.get_context_data()

    def get(self, request, object=None, **kwargs):
        context = self.get_context(request, object, **kwargs)
        if not context:
            return ''
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
    """
    content = None
    rel_attr = 'content'

    def get_content(self):
        if self.content is None:
            # FIXME: markdown?
            content = getattr(self.object, self.rel_attr)
            content = escape(content)
            content = re.sub(r'(^|\n\n)((\n?[^\n])+)', r'<p>\2</p>', content)
            content = re.sub(r'\n', r'<br>', content)
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
    detail_url = None

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
        if not self.detail_url and hasattr(post, 'detail_url'):
            self.detail_url = post.detail_url()


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

    fields = [ 'date', 'time', 'image', 'title', 'content', 'info' ]
    image_size = '64x64'
    truncate = 16

    def __init__ (self, items = None, *args, **kwargs):
        """
        If posts is given, create the object_list with instances
        of ListItem.
        """
        super().__init__(*args, **kwargs)
        self.add_css_class('list')
        if type(self) != Section:
            self.add_css_class('section_' + type(self).__name__.lower())

        if items:
            self.object_list = [
                ListItem(item) for item in items
            ]

    def get_object_list(self):
        return self.object_list

    def get_context_data(self):
        object_list = self.object_list or self.get_object_list()
        if not object_list and not self.message_empty:
            return

        context = super().get_context_data()
        context.update({
            'base_template': 'aircox/cms/section.html',
            'list': self,
            'object_list': object_list,
        })
        return context


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
            return models.Comment.route_url(routes.ThreadRoute, {
                'pk': self.object.id,
                'thread_model': self.object._website.name_of_model(
                    self.object.__class__
                ),
            })
        return ''

    def get_context_data(self):
        comment_form = None
        if self.object:
            post = self.object
            if hasattr(post, 'allow_comments') and post.allow_comments:
                comment_form = (self.comment_form or CommentForm())

        context = super().get_context_data()
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
    template_name = 'aircox/cms/section.html'
    tag = 'nav'
    classes = ''
    attrs = ''
    name = ''
    position = ''   # top, left, bottom, right, header, footer, page_top, page_bottom
    sections = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.css_class += ' menu menu_{}'.format(self.name or self.position)
        if not self.attrs:
            self.attrs = {}

    def get_context_data(self):
        return {
            'tag': self.tag,
            'css_class': self.css_class,
            'attrs': self.attrs,
            'content': ''.join([
                section.get(request=self.request, object=self.object)
                for section in self.sections
            ])
        }




