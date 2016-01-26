from django.db                      import models
from django.shortcuts               import render
from django.core.serializers.json   import DjangoJSONEncoder
from django.utils                   import timezone, dateformat

from django.views.generic           import ListView
from django.views.generic           import DetailView
from django.utils.translation       import ugettext as _, ugettext_lazy

from aircox.programs.models                import *
import aircox.programs.settings
import aircox.programs.utils





