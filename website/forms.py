from django import forms
from django.contrib.admin import widgets

import autocomplete_light.shortcuts as al
from autocomplete_light.contrib.taggit_field import TaggitWidget

from aircox.programs.models import *


class TrackForm (forms.ModelForm):
    class Meta:
        model = Track
        fields = ['artist', 'name', 'tags', 'position']
        widgets = {
            'artist': al.TextWidget('TrackArtistAutocomplete'),
            'name': al.TextWidget('TrackNameAutocomplete'),
            'tags': TaggitWidget('TagAutocomplete'),
        }

