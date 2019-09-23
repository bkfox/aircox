from django import template
from django.contrib import admin

register = template.Library()

@register.simple_tag(name='get_admin_tools')
def do_get_admin_tools():
    return admin.site.get_tools()

