import autocomplete_light.shortcuts as al
from programs.models import *


class SoundAutocomplete(al.AutocompleteModelBase):
    search_fields = ['title', 'file']
    model = Sound

al.register(SoundAutocomplete)


class TrackAutocomplete(al.AutocompleteModelBase):
    search_fields = ['artist', 'title']
    model = Track

al.register(TrackAutocomplete)


class ArticleAutocomplete(al.AutocompleteModelBase):
    search_fields = ['title', 'subtitle']
    model = Article

al.register(ArticleAutocomplete)


class ProgramAutocomplete(al.AutocompleteModelBase):
    search_fields = ['title', 'subtitle']
    model = Program

al.register(ProgramAutocomplete)


class EpisodeAutocomplete(al.AutocompleteModelBase):
    search_fields = ['title', 'subtitle']
    model = Episode

al.register(EpisodeAutocomplete)



