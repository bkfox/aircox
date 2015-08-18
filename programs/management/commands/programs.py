import argparse
import json

from django.core.management.base    import BaseCommand, CommandError
from django.utils                   import timezone
import programs.models              as models


class Model:
    # dict: key is the argument name, value is the constructor
    required = {}
    optional = {}
    model = None


    def __init__ (self, model, required = {}, optional = {}, post = None):
        self.model = model
        self.required = required
        self.optional = optional
        self.post = post


    def to_string (self):
        return '\n'.join(
                    [ '    - required: {}'.format(', '.join(self.required))
                    , '    - optional: {}'.format(', '.join(self.optional))
                    , (self.post is AddTags and '    - tags available\n') or
                        '\n'
                    ])

    def check_or_raise (self, options):
        for req in self.required:
            if req not in options:
                raise CommandError('required argument ' + req + ' is missing')


    def get_kargs (self, options):
        kargs = {}

        for i in self.required:
            if options.get(i):
                fn = self.required[i]
                kargs[i] = fn(options[i])

        for i in self.optional:
            if options.get(i):
                fn = self.optional[i]
                kargs[i] = fn(options[i])

        return kargs


    def get_by_id (self, options):
        id_list = options.get('id')
        items = self.model.objects.filter( id__in = id_list )

        if len(items) is not len(id_list):
            for key, id in enumerate(id_list):
                if id in items:
                    del id_list[key]
            raise CommandError(
                    'the following ids has not been found: {} (no change done)'
                    , ', '.join(id_list)
                    )

        return items


    def make (self, options):
        self.check_or_raise(options)

        kargs    = self.get_kargs(options)
        item = self.model(**kargs)
        item.save()

        if self.post:
            self.post(item, options)

        print('{} #{} created'.format(self.model.name()
                                     , item.id))


    def update (self, options):
        items = self.get_by_id(options)

        for key, item in enumerate(items):
            kargs = self.get_kargs(options)
            item.__dict__.update(options)
            item.save()
            print('{} #{} updated'.format(self.model.name()
                                         , item.id))
            del items[key]


    def delete (self, options):
        items = self.get_by_id(options)
        items.delete()
        print('{} #{} deleted'.format(self.model.name()
                                     , ', '.join(options.get('id'))
                                     ))


    def dump (self, options):
        qs = self.model.objects.all()
        fields = ['id'] + [ f.name for f in self.model._meta.fields
                                if f.name is not 'id']
        items = []
        for item in qs:
            r = []
            for f in fields:
                v = getattr(item, f)
                if hasattr(v, 'id'):
                    v = v.id
                r.append(v)
            items.append(r)

        if options.get('head'):
            items = items[0:options.get('head')]
        elif options.get('tail'):
            items = items[-options.get('tail'):]

        if options.get('json'):
            if options.get('fields'):
                print(json.dumps(fields))
            print(json.dumps(items, default = lambda x: str(x)))
            return

        if options.get('fields'):
            print(' || '.join(fields))
        for item in items:
            print(' || '.join(item))


def DateTime (string):
    dt = timezone.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    return timezone.make_aware(dt, timezone.get_current_timezone())


def Time (string):
    dt = timezone.datetime.strptime(string, '%H:%M')
    return timezone.datetime.time(dt)


def AddTags (instance, options):
    if options.get('tags'):
        instance.tags.add(*options['tags'])


models = {
    'program': Model( models.Program
                    , { 'title': str }
                    , { 'subtitle': str, 'can_comment': bool, 'date': DateTime
                      , 'parent_id': int, 'public': bool
                      , 'url': str, 'email': str, 'non_stop': bool
                      }
                    , AddTags
                    )
  , 'article': Model( models.Article
                    , { 'title': str }
                    , { 'subtitle': str, 'can_comment': bool, 'date': DateTime
                      , 'parent_id': int, 'public': bool
                      , 'static_page': bool, 'focus': bool
                      }
                    , AddTags
                    )
  , 'episode': Model( models.Episode
                    , { 'title': str }
                    , { 'subtitle': str, 'can_comment': bool, 'date': DateTime
                      , 'parent_id': int, 'public': bool
                      }
                    , AddTags
                    )
  , 'schedule': Model( models.Schedule
                    , { 'parent_id': int, 'date': DateTime, 'duration': Time
                      , 'frequency': int }
                    , { 'rerun': int } # FIXME: redo
                    )
  , 'soundfile': Model( models.SoundFile
                    , { 'parent_id': int, 'date': DateTime, 'file': str
                      , 'duration': Time}
                    , { 'fragment': bool, 'embed': str, 'removed': bool }
                    , AddTags
                    )
}



class Command (BaseCommand):
    help='Create, update, delete or dump an element of the given model.' \
         ' If no action is given, dump it'


    def add_arguments (self, parser):
        parser.add_argument( 'model', type=str
                           , metavar="MODEL"
                           , help='model to add. It must be in {}'\
                                    .format(', '.join(models.keys()))
                           )

        group = parser.add_argument_group('actions')
        group.add_argument('--dump', action='store_true')
        group.add_argument('--add', action='store_true'
                          , help='create or update (if id is given) object')
        group.add_argument('--delete', action='store_true')
        group.add_argument('--json', action='store_true'
                          , help='dump using json')


        group = parser.add_argument_group('selector')
        group.add_argument('--id', type=str, nargs='+'
                          , metavar="ID"
                          , help='select existing object by id'
                          )
        group.add_argument('--head', type=int
                          , help='dump the HEAD first objects only'
                          )
        group.add_argument('--tail', type=int
                          , help='dump the TAIL last objects only'
                          )
        group.add_argument('--fields', action='store_true'
                          , help='print fields before dumping'
                          )


        # publication/generic
        group = parser.add_argument_group('fields'
                        , 'depends on the given model')
        group.add_argument('--parent_id',  type=str)
        group.add_argument('--title',      type=str)
        group.add_argument('--subtitle',   type=str)
        group.add_argument('--can_comment',action='store_true')
        group.add_argument('--public',     action='store_true')
        group.add_argument( '--date',      type=str
                          , help='a valid date time (Y/m/d H:m:s')
        group.add_argument('--tags',       type=str, nargs='+')

        # program
        group.add_argument('--url',        type=str)
        group.add_argument('--email',      type=str)
        group.add_argument('--non_stop',   type=int)

        # article
        group.add_argument('--static_page',action='store_true')
        group.add_argument('--focus',      action='store_true')

        # schedule
        group.add_argument('--duration',   type=str)
        group.add_argument('--frequency',  type=int)
        group.add_argument('--rerun',      type=int)

        # fields
        parser.formatter_class=argparse.RawDescriptionHelpFormatter
        parser.epilog = 'available fields per model:'
        for name, model in models.items():
            parser.epilog += '\n  ' + model.model.type() + ': \n' \
                           + model.to_string()


    def handle (self, *args, **options):
        model = options.get('model')
        if not model:
            raise CommandError('no model has been given')

        model = model.lower()
        if model not in models:
            raise CommandError('model {} is not supported'.format(str(model)))

        if options.get('add'):
            if options.get('id'):
                models[model].update(options)
            else:
                models[model].make(options)
        elif options.get('delete'):
            models[model].delete(options)
        else: # --dump --json
            models[model].dump(options)


