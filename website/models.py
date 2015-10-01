from django.db import models

from cms.models import RelatedPost
import programs.models as programs

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

