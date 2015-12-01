import autocomplete_light.shortcuts as al
from aircox.programs.models import *

from taggit.models import Tag
al.register(Tag)


class OneFieldAutocomplete(al.AutocompleteModelBase):
    choice_html_format = u'''
        <span class="block" data-value="%s">%s</span>
    '''

    def choice_html (self, choice):
        value = choice[self.search_fields[0]]
        return self.choice_html_format % (self.choice_label(choice),
            self.choice_label(value))


    def choices_for_request(self):
        #if not self.request.user.is_staff:
        #    self.choices = self.choices.filter(private=False)
        filter_args = { self.search_fields[0] + '__icontains': self.request.GET['q'] }

        self.choices = self.choices.filter(**filter_args)
        self.choices = self.choices.values(self.search_fields[0]).distinct()
        return self.choices


class TrackArtistAutocomplete(OneFieldAutocomplete):
    search_fields = ['artist']
    model = Track

al.register(TrackArtistAutocomplete)


class TrackNameAutocomplete(OneFieldAutocomplete):
    search_fields = ['name']
    model = Track


al.register(TrackNameAutocomplete)


#class DiffusionAutocomplete(OneFieldAutocomplete):
#    search_fields = ['episode', 'program', 'start', 'stop']
#    model = Diffusion
#
#al.register(DiffusionAutocomplete)


