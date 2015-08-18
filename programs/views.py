from django.shortcuts               import render
from django.core.serializers.json   import DjangoJSONEncoder
from django.utils                   import timezone, dateformat

import programs.models              as models
import programs.settings



class DiffusionList:
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
        diffusions = models.Diffusion.objects;

        if self.next:   diffusions = diffusions.filter( date_end__ge = timezone.now() )
        elif self.prev: diffusions = diffusions.filter( date_end__le = timezone.now() )
        else:           diffusions = diffusions.all()

        diffusions = diffusions.extra(order_by = ['date'])
        if self.at:     diffusions = diffusions[self.at:]
        if self.count:  diffusions = diffusions[:self.count]

        self.diffusions = diffusions


    def raw_string():
        """
        Return a string with diffusions rendered as raw
        """
        res = []
        for diffusion in diffusions:
            r = [ dateformat.format(diffusion.date, "Y/m/d H:i:s")
                , str(diffusion.type)
                , diffusion.parent.file.path
                , diffusion.parent.file.url
                ]

            res.push(' '.join(r))

        return '\n'.join(res)


    def json_string():
        import json

        res = []
        for diffusion in diffusions:
            r = {
                  'date': dateformat.format(diffusion.date, "Y/m/d H:i:s")
                , 'date_end': dateformat.format(diffusion.date_end, "Y/m/d H:i:s")
                , 'type': str(diffusion.type)
                , 'file_path': diffusion.parent.file.path
                , 'file_url': diffusion.parent.file.url
                }

            res.push(json.dumps(r))

        return '\n'.join(res)






