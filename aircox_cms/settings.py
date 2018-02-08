import os

from django.conf import settings

AIRCOX_CMS_BLEACH_COMMENT_TAGS = [
    'i', 'emph', 'b', 'strong', 'strike', 's',
    'p', 'span', 'quote','blockquote','code',
    'sup', 'sub', 'a',
]

AIRCOX_CMS_BLEACH_COMMENT_ATTRS = {
    '*': ['title'],
    'a': ['href', 'rel'],
}


# import settings
for k, v in settings.__dict__.items():
    if not k.startswith('__') and k not in globals():
        globals()[k] = v


