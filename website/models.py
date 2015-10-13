from django.db import models

from aircox_cms.models import RelatedPost
import aircox_programs.models as programs

class Program (RelatedPost):
    class Relation:
        related_model = programs.Program
        bind_mapping = True
        mapping = {
            'title': 'name',
            'content': 'description',
        }

class Episode (RelatedPost):
    class Relation:
        related_model = programs.Episode
        bind_mapping = True
        mapping = {
            'thread': 'program',
            'title': 'name',
            'content': 'description',
        }

