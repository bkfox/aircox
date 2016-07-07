"""
Actions are used to add controllers available to the end user.
They are attached to models, and tested (+ rendered if it is okay)
before rendering each instance of the models.

For the moment it only can execute javascript code. There is also
a javascript mini-framework in order to make it easy. The code of
the action is then registered and executable on users actions.
"""
class Actions(type):
    """
    General class that is used to register and manipulate actions
    """
    registry = []

    def __new__(cls, name, bases, attrs):
        cl = super().__new__(cls, name, bases, attrs)
        if name != 'Action':
            cls.registry.append(cl)
        return cl

    @classmethod
    def make(cl, request, object_list = None, object = None):
        """
        Make action on the given object_list or object
        """
        if object_list:
            in_list = True
        else:
            object_list = [object]
            in_list = False

        for object in object_list:
            if not hasattr(object, 'actions') or not object.actions:
                continue
            object.actions = [
                action.test(request, object, in_list)
                if type(action) == cl and issubclass(action, Action) else
                str(action)
                for action in object.actions
            ]
            object.actions = [ code for code in object.actions if code ]

    @classmethod
    def register_code(cl):
        """
        Render javascript code that can be inserted somewhere to register
        all actions
        """
        return '\n'.join(action.register_code() for action in cl.registry)


class Action(metaclass=Actions):
    """
    An action available to the end user.
    Don't forget to note in docstring the needed things.
    """
    id = ''
    """
    Unique ID for the given action
    """
    symbol = ''
    """
    UTF-8 symbol for the given action
    """
    title = ''
    """
    Used to render the correct button for the given action
    """
    code = ''
    """
    If set, used as javascript code executed when the action is
    activated
    """

    @classmethod
    def register_code(cl):
        """
        Render a Javascript code that append the code to the available actions.
        Used by Actions
        """
        if not cl.code:
            return ''

        return """
        Actions.register('{cl.id}', '{cl.symbol}', '{cl.title}', {cl.code})
        """.format(cl = cl)

    @classmethod
    def has_me(cl, object):
        return hasattr(object, 'actions') and cl.id in object.actions

    @classmethod
    def to_str(cl, object, url = None, **data):
        """
        Utility class to add the action on the object using the
        given data.
        """
        if cl.has_me(object):
            return

        code = \
            '<a class="action" {onclick} action="{cl.id}" {data} title="{cl.title}">' \
            '{cl.symbol}<label>{cl.title}</label>' \
            '</a>'.format(
                href = '' if not url else 'href="' + url + '"',
                onclick = 'onclick="return Actions.run(event, \'{cl.id}\');"' \
                              .format(cl = cl)
                          if cl.id and cl.code else '',
                data = ' '.join('data-{k}="{v}"'.format(k=k, v=v)
                                for k,v in data.items()),
                cl = cl
            )

        return code

    @classmethod
    def test(cl, request, object, in_list):
        """
        Test if the given object can have the generated action. If yes, return
        the generated content, otherwise, return None

        in_list: object is rendered in a list
        """


