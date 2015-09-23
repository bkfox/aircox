from django.db import models
from django.utils import timezone, dateformat
from programs.models import *


class ListQueries:
    @staticmethod
    def search (qs, q):
        qs = qs.filter(tags__slug__in = re.compile(r'(\s|\+)+').split(q)) | \
             qs.filter(title__icontains = q) | \
             qs.filter(subtitle__icontains = q) | \
             qs.filter(content__icontains = q)
        qs.distinct()
        return qs

    @staticmethod
    def thread (qs, q):
        return qs.filter(parent = q)

    @staticmethod
    def next (qs, q):
        qs = qs.filter(date__gte = timezone.now())
        if q:
            qs = qs.filter(parent = q)
        return qs

    @staticmethod
    def prev (qs, q):
        qs = qs.filter(date__lte = timezone.now())
        if q:
            qs = qs.filter(parent = q)
        return qs

    @staticmethod
    def date (qs, q):
        if not q:
            q = timezone.datetime.today()
        if type(q) is str:
            q = timezone.datetime.strptime(q, '%Y%m%d').date()

        return qs.filter(date__startswith = q)

    class Diffusion:
        @staticmethod
        def episode (qs, q):
            return qs.filter(episode = q)

        @staticmethod
        def program (qs, q):
            return qs.filter(program = q)

class ListQuery:
    model = None
    qs = None

    def __init__ (self, model, *kwargs):
        self.model = model
        self.__dict__.update(kwargs)

    def get_queryset (self, by, q):
        qs = model.objects.all()
        if model._meta.get_field_by_name('public'):
            qs = qs.filter(public = True)

        # run query set
        queries = Queries.__dict__.get(self.model) or Queries
        filter = queries.__dict__.get(by)
        if filter:
            qs = filter(qs, q)

        # order
        if self.sort == 'asc':
            qs = qs.order_by('date', 'id')
        else:
            qs = qs.order_by('-date', '-id')

        # exclude
        qs = qs.exclude(id = exclude)

        self.qs = qs
        return qs


