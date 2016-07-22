import os

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


ensure('AIRCOX_CMS_BLEACH_COMMENT_TAGS', [
    'i', 'emph', 'b', 'strong', 'strike', 's',
    'p', 'span', 'quote','blockquote','code',
    'sup', 'sub', 'a',
])

ensure('AIRCOX_CMS_BLEACH_COMMENT_ATTRS', {
    '*': ['title'],
    'a': ['href', 'rel'],
})


