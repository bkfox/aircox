from django.db import models

from aircox_cms.models import RelatedPost
import aircox_programs.models as programs

class Program (RelatedPost):
    class Relation:
        related_model = programs.Program
        mapping = {
            'title': 'name',
            'content': 'description',
        }

class Episode (RelatedPost):
    class Relation:
        related_model = programs.Episode
        mapping = {
            'title': 'name',
            'content': 'description',
        }

