from django.db import models

from aircox.cms.models import RelatedPost
import aircox.programs.models as programs

class Program (RelatedPost):
    class Relation:
        model = programs.Program
        bind_mapping = True
        mapping = {
        }

class Episode (RelatedPost):
    class Relation:
        model = programs.Diffusion
        bind_mapping = True
        mapping = {
            'thread': 'program',
            # 'title': 'name',
            # 'content': 'description',
        }

