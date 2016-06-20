import operator
import itertools
import heapq

from django.db.models.query import QuerySet

class QCombine:
    """
    This class helps to combine querysets of different models and lists of
    object, and to iter over it.

    Notes:
    - when working on fields, we assume that they exists on all of them;
    - for efficiency, there is no possibility to change order per field;
      to do so, do it directly on the querysets
    """
    order_fields = None
    lists = None

    def __init__(self, *lists):
        """
        lists: list of querysets that are used to initialize the stuff.
        """
        self.lists = lists or []

    def filter(self, **kwargs):
        for qs in self.lists:
            if issubclass(type(qs), QuerySet):
                qs.filter(**kwargs)
        return self

    def exclude(self, **kwargs):
        for qs in self.lists:
            if issubclass(type(qs), QuerySet):
                qs.exclude(**kwargs)
        return self

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

        for qs in self.lists:
            if issubclass(type(qs), QuerySet):
                qs.order_by(*fields)
            else:
                qs.sort(key = operator.attrgetter(fields),
                        reverse = reverse)
        return self

    def __len__(self):
        return sum([len(qs) for qs in self.lists])

    def __iter__(self):
        if self.order_fields:
            return heapq.merge(
                *self.lists,
                key = operator.attrgetter(*self.order_fields),
                reverse = self.order_reverse
            )
        return itertools.chain(self.lists)

    def __getitem__(self, k):
        if type(k) == slice:
            return list(itertools.islice(iter(self), k.start, k.stop, k.step))
        return list(itertools.islice(iter(self), k))

