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


    def check_or_raise (self, options):
        for req in self.required:
            if req not in options:
                raise ValueError('required argument ' + req + ' is missing')


    def get_kargs (self, options):
        kargs = {}

        for i in self.required:
            if options.get(i):
                fn = self.required[i]
                kargs[i] = fn(options[i])

        for i in self.optional:
            if options.get(i):
                print(i, options)
                fn = self.optional[i]
                kargs[i] = fn(options[i])

        return kargs


    def make (self, options):
        self.check_or_raise(options)

        kargs    = self.get_kargs(options)
        instance = self.model(**kargs)
        instance.save()

        if self.post:
            self.post(instance, options)

        print(instance.__dict__)


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
  , 'schedule': Model( models.Schedule
                    , { 'parent_id': int, 'date': DateTime, 'duration': Time
                      , 'frequency': int }
                    , { 'rerun': bool }
                    )
}



class Command (BaseCommand):
    help="Add an element of the given model"


    def add_arguments (self, parser):
        parser.add_argument( 'model', type=str
                           , metavar="MODEL"
                           , help="model to add. It must be in [schedule,program,article]")

        # publication/generic
        parser.add_argument('--parent_id',  type=str)
        parser.add_argument('--title',      type=str)
        parser.add_argument('--subtitle',   type=str)
        parser.add_argument('--can_comment',action='store_true')
        parser.add_argument('--public',     action='store_true')
        parser.add_argument( '--date',      type=str
                           , help='a valid date time (Y/m/d H:m:s')
        parser.add_argument('--tags',       type=str, nargs='+')

        # program
        parser.add_argument('--url',        type=str)
        parser.add_argument('--email',      type=str)
        parser.add_argument('--non_stop',   type=int)

        # article
        parser.add_argument('--static_page',action='store_true')
        parser.add_argument('--focus',      action='store_true')

        # schedule
        parser.add_argument('--duration',   type=str)
        parser.add_argument('--frequency',  type=int)
        parser.add_argument('--rerun',      action='store_true')


    def handle (self, *args, **options):
        model = options.get('model')
        if not model:
            return

        model = model.lower()
        if model not in models:
            raise ValueError("model {} is not supported".format(str(model)))

        models[model].make(options)


