from django import forms
from django.forms import ModelForm

from .models import Comment


class CommentForm(ModelForm):
    nickname = forms.CharField()
    email = forms.EmailField(required=False)
    content = forms.CharField(widget=forms.Textarea())

    nickname.widget.attrs.update({'class': 'input'})
    email.widget.attrs.update({'class': 'input'})
    content.widget.attrs.update({'class': 'textarea'})

    class Meta:
        model = Comment
        fields = ['nickname', 'email', 'content']


