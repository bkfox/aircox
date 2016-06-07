from django import forms

#import autocomplete_light.shortcuts as al
#from autocomplete_light.contrib.taggit_field import TaggitWidget

import aircox.programs.models as programs


class TrackForm (forms.ModelForm):
    class Meta:
        model = programs.Track
        fields = ['artist', 'name', 'tags', 'position']
        widgets = {
#            'artist': al.TextWidget('TrackArtistAutocomplete'),
#            'name': al.TextWidget('TrackNameAutocomplete'),
#            'tags': TaggitWidget('TagAutocomplete'),
        }


