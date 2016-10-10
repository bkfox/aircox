import django.forms as forms
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.exceptions import ValidationError

from honeypot.decorators import verify_honeypot_value

import aircox.cms.models as models


class CommentForm(forms.ModelForm):
    class Meta:
        model  = models.Comment
        fields = ['author', 'email', 'url', 'content']
        localized_fields = '__all__'
        widgets = {
            'author': forms.TextInput(attrs={
                'placeholder': _('your name'),
            }),
            'email': forms.TextInput(attrs={
                'placeholder': _('your email (optional)'),
            }),
            'url': forms.URLInput(attrs={
                'placeholder': _('your website (optional)'),
            }),
            'comment': forms.TextInput(attrs={
                'placeholder': _('your comment'),
            })
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.page = kwargs.pop('object', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.request:
            if verify_honeypot_value(self.request, 'hp_website'):
                raise ValidationError(_('You are a bot, that is not cool'))

            if not self.object:
                raise ValidationError(_('No publication found for this comment'))


