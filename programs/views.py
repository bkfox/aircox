from django.shortcuts               import render
from django.core.serializers.json   import DjangoJSONEncoder
from django.utils                   import timezone, dateformat

import programs.models              as models
import programs.settings



class EventList:
    type  = None
    next  = None
    prev  = None
    at    = None
    count = None


    def __init__ (self, **kwargs):
        self.__dict__ = kwargs
        if kwargs:
            self.get_queryset()


    def get_queryset (self):
        events = models.Event.objects;

        if self.next:   events = events.filter( date_end__ge = timezone.now() )
        elif self.prev: events = events.filter( date_end__le = timezone.now() )
        else:           events = events.all()

        events = events.extra(order_by = ['date'])
        if self.at:     events = events[self.at:]
        if self.count:  events = events[:self.count]

        self.events = events


    def raw_string():
        """
        Return a string with events rendered as raw
        """
        res = []
        for event in events:
            r = [ dateformat.format(event.date, "Y/m/d H:i:s")
                , str(event.type)
                , event.parent.file.path
                , event.parent.file.url
                ]

            res.push(' '.join(r))

        return '\n'.join(res)


    def json_string():
        import json

        res = []
        for event in events:
            r = {
                  'date': dateformat.format(event.date, "Y/m/d H:i:s")
                , 'date_end': dateformat.format(event.date_end, "Y/m/d H:i:s")
                , 'type': str(event.type)
                , 'file_path': event.parent.file.path
                , 'file_url': event.parent.file.url
                }

            res.push(json.dumps(r))

        return '\n'.join(res)






