import datetime

from django.utils.safestring import mark_safe
from django.urls.converters import StringConverter


class PagePathConverter(StringConverter):
    """ Match path for pages, including surrounding slashes. """
    regex = r'/?|([-_a-zA-Z0-9]+/)*?'

    def to_python(self, value):
        if not value or value[0] != '/':
            value = '/' + value
        if len(value) > 1 and value[-1] != '/':
            value = value + '/'
        return value

    def to_url(self, value):
        if value[0] == '/':
            value = value[1:]
        if value[-1] != '/':
            value = value + '/'
        return mark_safe(value)


#class WeekConverter:
#    """ Converter for date as YYYYY/WW """
#    regex = r'[0-9]{4}/[0-9]{2}/?'
#
#    def to_python(self, value):
#        value = value.split('/')
#        return datetime.date(int(value[0]), int(value[1]), int(value[2]))
#
#    def to_url(self, value):
#        return '{:04d}/{:02d}/'.format(*value.isocalendar())


class DateConverter:
    """ Converter for date as YYYY/MM/DD """
    regex = r'[0-9]{4}/[0-9]{2}/[0-9]{2}/?'

    def to_python(self, value):
        value = value.split('/')
        return datetime.date(int(value[0]), int(value[1]), int(value[2]))

    def to_url(self, value):
        return '{:04d}/{:02d}/{:02d}/'.format(value.year, value.month,
                                              value.day)

