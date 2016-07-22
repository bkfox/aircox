from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from aircox.cms.models import *


def index_page(request):
    context = {}
    if ('tag' or 'search') in request.GET:
        qs = Publication.get_queryset(request, context = context)

    return render(request, 'index_page.html', context)

