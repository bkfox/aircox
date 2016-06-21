import operator
import itertools
import heapq

from django.utils.translation import ugettext as _, ugettext_lazy
from django.db.models.query import QuerySet

from aircox.cms.models import Routable


class QCombine:
    """
    This class helps to combine querysets of different models and lists of
    object, and to iter over it.

    Notes:
    - when working on fields, we assume that they exists on all of them;
    - for efficiency, there is no possibility to change order per field;
      to do so, do it directly on the querysets
    - we dont clone the combinator in order to avoid overhead
    """
    order_fields = None
    lists = None

    def __init__(self, *lists):
        """
        lists: list of querysets that are used to initialize the stuff.
        """
        self.lists = list(lists) or []

    def map(self, qs_func, non_qs = None):
        """
        Map results of qs_func for QuerySet instance and of non_qs for
        the others (if given), because QuerySet always clones itself.
        """
        for i, qs in enumerate(self.lists):
            if issubclass(type(qs), QuerySet):
                self.lists[i] = qs_func(qs)
            elif non_qs:
                self.lists[i] = non_qs(qs)

    def all(self):
        self.map(lambda qs: qs.all())

    def filter(self, **kwargs):
        self.map(lambda qs: qs.filter(**kwargs))
        return self

    def exclude(self, **kwargs):
        self.map(lambda qs: qs.exclude(**kwargs))
        return self

    def distinct(self, **kwargs):
        self.map(lambda qs: qs.distinct())
        return self

    def get(self, **kwargs):
        self.filter(**kwargs)
        it = iter(self)
        return next(it)

    def order_by(self, *fields, reverse = False):
        """
        Order using these fields. For compatibility, if there is
        at least one fields whose name starts with '-', reverse
        the order
        """
        for i, field in enumerate(fields):
            if field[0] == '-':
                reverse = True
                fields[i] = field[1:]

        self.order_reverse = reverse
        self.order_fields = fields
        self.map(
            lambda qs: qs.order_by(*fields),
            lambda qs: sorted(
                qs,
                qs.sort(
                    key = operator.attrgetter(*fields),
                    reverse = reverse
                )
            )
        )
        return self

    def clone(self):
        """
        Make a clone of the class. Not that lists are copied, non-deeply
        """
        return QCombine(*[
            qs.all() if issubclass(type(qs), QuerySet) else qs.copy()
            for qs in self.lists
        ])

    def __len__(self):
        return sum([len(qs) for qs in self.lists])

    def __iter__(self):
        if not self.order_fields:
            return itertools.chain(self.lists)

        # FIXME: need it lazy?
        return heapq.merge(
            *self.lists,
            key = operator.attrgetter(*self.order_fields),
            reverse = self.order_reverse
        )

    def __getitem__(self, k):
        if type(k) == slice:
            it = itertools.islice(iter(self), k.start, k.stop, k.step)
        else:
            it = itertools.islice(iter(self), k)
        return list(it)




class Manager(type):
    models = []

    @property
    def objects(self):
        qs = QCombine(*[model.objects.all() for model in self.models])
        return qs


class FakeModel(Routable,metaclass=Manager):
    """
    This class is used to register a route for multiple models to a website.
    A QCombine is created with qs for all given models when objects
    property is retrieved.

    Note: there no other use-case.
    """
    class Meta:
        verbose_name = _('publication')
        verbose_name_plural = _('publications')

    _meta = Meta()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

