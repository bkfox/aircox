import datetime

# django
from django.db                              import models
from django.contrib.auth.models             import User
from django.template.defaultfilters         import slugify

from django.http                            import HttpResponse, Http404

from django.contrib.contenttypes.fields     import GenericForeignKey
from django.contrib.contenttypes.models     import ContentType

from django.shortcuts                       import get_object_or_404
from django.utils.translation               import ugettext as _, ugettext_lazy
from django.utils                           import timezone
from django.utils.html                      import strip_tags

from django.conf                            import settings

# extensions
from taggit.managers                        import TaggableManager


import programs.settings                    as settings



AFrequency = {
    'ponctual':          0x000000,
    'every week':        0b001111,
    'first week':        0x000001,
    'second week':       0x000010,
    'third week':        0x000100,
    'fourth week':       0x001000,
    'first and third':   0x000101,
    'second and fourth': 0x001010,
    'one week on two':   0x010010,
    #'uneven week':         0x100000,
    # TODO 'every day':     0x110000
}


# Translators: html safe values
ugettext_lazy('ponctual')
ugettext_lazy('every week')
ugettext_lazy('first week')
ugettext_lazy('second week')
ugettext_lazy('third week')
ugettext_lazy('fourth week')
ugettext_lazy('first and third')
ugettext_lazy('second and fourth')
ugettext_lazy('one week on two')


Frequency = [ (y, x) for x,y in AFrequency.items() ]
RFrequency = { y: x for x,y in AFrequency.items() }

Frequency.sort(key = lambda e: e[0])


class Model (models.Model):
    @classmethod
    def type (cl):
        """
        Return a string with the type of the model (class name lowered)
        """
        name = cl.__name__.lower()
        return name

    @classmethod
    def type_plural (cl):
        """
        Return a string with the name in plural of the model (cf. name())
        """
        return cl.type() + 's'


    @classmethod
    def name (cl, plural = False):
        """
        Return the name of the model using meta.verbose_name
        """
        if plural:
            return cl._meta.verbose_name_plural.title()
        return cl._meta.verbose_name.title()


    class Meta:
        abstract = True



class Metadata (Model):
    """
    meta is used to extend a model for future needs
    """
    author      = models.ForeignKey (
                      User
                    , verbose_name = _('author')
                    , blank = True
                    , null = True
                  )
    title       = models.CharField(
                      _('title')
                    , max_length = 128
                  )
    date        = models.DateTimeField(
                      _('date')
                    , default = datetime.datetime.now
                  )
    public      = models.BooleanField(
                      _('public')
                    , default = False
                    , help_text = _('publication is accessible to the public')
                  )
    meta        = models.TextField(
                      _('meta')
                    , blank = True
                    , null = True
                  )
    tags        = TaggableManager(
                      _('tags')
                    , blank = True
                  )

    class Meta:
        abstract = True



class Publication (Metadata):
    def get_slug_name (self):
        return slugify(self.title)

    def __str__ (self):
        return self.title + ' (' + str(self.id) + ')'

    subtitle    = models.CharField(
                      _('subtitle')
                    , max_length = 128
                    , blank = True
                  )
    img         = models.ImageField(
                      _('image')
                    , upload_to = "images"
                    , blank = True
                  )
    content     = models.TextField(
                      _('content')
                    , blank = True
                  )
    can_comment = models.BooleanField(
                      _('enable comments')
                    , default = True
                    , help_text = _('comments are enabled on this publication')
                  )

    #
    # Class methods
    #
    @staticmethod
    def _exclude_args (allow_unpublished = False, prefix = ''):
        if allow_unpublished:
            return {}

        res = {}
        res[prefix + 'public'] = False
        res[prefix + 'date__gt'] = timezone.now()
        return res


    @classmethod
    def get_available (cl, first = False, **kwargs):
        """
        Return the result of filter(kargs) if the resulting publications
        is published and public

        Otherwise, return None
        """
        kwargs['public'] = True
        kwargs['date__lte'] = timezone.now()

        e = cl.objects.filter(**kwargs)

        if first:
            return (e and e[0]) or None
        return e or None


    #
    # Instance's methods
    #
    def get_parent (self, raise_404 = False ):
        if not parent and raise_404:
            raise Http404
        return parent


    def get_parents ( self, order_by = "desc", include_fields = None ):
        """
        Return an array of the parents of the item.
        If include_fields is an array of files to include.
        """
        # TODO: fields included
        # FIXME: parameter name + container
        parents = [ self ]
        while parents[-1].parent:
            parent = parents[-1].parent
            if parent not in parents:
                # avoid cycles
                parents.append(parent)

        parents = parents[1:]

        if order_by == 'desc':
            return reversed(parents)
        return parents


    class Meta:
        abstract = True



#
# Usable models
#
class Track (Model):
    artist      = models.CharField(
                      _('artist')
                    , max_length = 128
                    , blank = True
                  )
    title       = models.CharField(
                      _('title')
                    , max_length = 128
                  )
    version     = models.CharField(
                      _('version')
                    , max_length = 128
                    , blank = True
                    , help_text = _('additional informations on that track')
                  )
    tags        = TaggableManager( blank = True )


    def __str__(self):
        return ' '.join([self.title, _('by'), self.artist,
                (self.version and ('(' + self.version + ')') or '') ])


    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')



class SoundFile (Metadata):
    parent      = models.ForeignKey(
                      'Episode'
                    , verbose_name = _('episode')
                    , blank = True
                    , null = True
                  )
    file        = models.FileField(
                      _('file')
                    , upload_to = "data/tracks"
                    , blank = True
                  )
    duration    = models.TimeField(
                      _('duration')
                    , blank = True
                    , null = True
                  )
    fragment    = models.BooleanField(
                      _('incomplete sound')
                    , default = False
                    , help_text = _("the file has been cut")
                  )
    embed       = models.TextField (
                      _('embed HTML code from external website')
                    , blank = True
                    , null = True
                    , help_text = _('if set, consider the sound podcastable from there')
                  )


    def __str__ (self):
        return str(self.id) + ': ' + self.file.name


    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')



class Schedule (Model):
    parent      = models.ForeignKey( 'Program', blank = True, null = True )
    date        = models.DateTimeField(_('start'))
    duration    = models.TimeField(_('duration'))
    frequency   = models.SmallIntegerField(_('frequency'), choices = Frequency)
    rerun       = models.BooleanField(_('rerun'), default = False)


    def match_week (self, at = datetime.date.today()):
        """
        Return True if the given week number matches the schedule, False
        otherwise.
        If the schedule is ponctual, return None.
        """
        if self.frequency == AFrequency['ponctual']:
            return None

        if self.frequency == AFrequency['one week on two']:
            week = at.isocalendar()[1]
            return (week % 2) == (self.date.isocalendar()[1] % 2)

        first_of_month = datetime.date(at.year, at.month, 1)
        week = at.isocalendar()[1] - first_of_month.isocalendar()[1]

        # weeks of month
        if week == 4:
            # fifth week: return if for every week
            return self.frequency == 0b1111
        return (self.frequency & (0b0001 << week) > 0)



    def next_date (self, at = datetime.date.today()):
        if self.frequency == AFrequency['ponctual']:
            return None

        # first day of the week
        date = at - datetime.timedelta( days = at.weekday() )

        # for the next five week, we look for a matching week.
        # when found, add the number of day since de start of the
        # we need to test if the result is >= at
        for i in range(0,5):
            if self.match_week(date):
                date_ = date + datetime.timedelta( days = self.date.weekday() )
                if date_ >= at:
                    # we don't want past events
                    return datetime.datetime(date_.year, date_.month, date_.day,
                                                self.date.hour, self.date.minute)
            date += datetime.timedelta( days = 7 )
        else:
            return None


    def next_dates (self, at = datetime.date.today(), n = 52):
        # we could have optimized this function, but since it should not
        # be use too often, we keep a more readable and easier to debug
        # solution
        if self.frequency == 0b000000:
            return None

        res = []
        for i in range(n):
            e = self.next_date(at)
            if not e:
                break
            res.append(e)
            at = res[-1] + datetime.timedelta(days = 1)

        return res


    def to_string(self):
        s = ugettext_lazy( RFrequency[self.frequency] )
        if self.rerun:
            return s + ' (' + _('rerun') + ')'
        return s


    def __str__ (self):
        return self.parent.title + ': ' + RFrequency[self.frequency]


    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')




class Article (Publication):
    parent      = models.ForeignKey(
                      'self'
                    , verbose_name = _('parent')
                    , blank = True
                    , null = True
                  )
    static_page = models.BooleanField(
                      _('static page')
                    , default = False
                  )
    focus       = models.BooleanField(
                      _('article is focus')
                    , blank = True
                    , default = False
                  )


    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')



class Program (Publication):
    parent      = models.ForeignKey(
                      Article
                    , verbose_name = _('parent')
                    , blank = True
                    , null = True
                  )
    email       = models.EmailField(
                      _('email')
                    , max_length = 128
                    , null = True
                    , blank = True
                  )
    url         = models.URLField(
                    _('website')
                    , blank = True
                    , null = True
                  )
    tag         = models.CharField(
                      _('tag')
                    , max_length = 64
                    , help_text = _('used in articles to refer to it')
                  )

    @property
    def path(self):
        return settings.AIRCOX_PROGRAMS_DATA + slugify(self.title + '_' + self.id)


    class Meta:
        verbose_name = _('Program')
        verbose_name_plural = _('Programs')



class Episode (Publication):
    # Note:
    #   We do not especially need a duration here, because even if an
    #   emussion's schedule can have specified durations, in practice this
    #   duration may vary. Furthermore, we want the users have to enter a
    #   minimum of values.
    #   Duration can be retrieved from the sound file if there is one.
    #
    parent      = models.ForeignKey(
                      Program
                    , verbose_name = _('parent')
                    , blank = True
                    , null = True
                  )
    tracks      = models.ManyToManyField(
                      Track
                    , verbose_name = _('playlist')
                    , blank = True
                  )


    class Meta:
        verbose_name = _('Episode')
        verbose_name_plural = _('Episodes')



class Event (Model):
    """
    """
    parent      = models.ForeignKey (
                      Episode
                    , verbose_name = _('episode')
                    , blank = True
                    , null = True
                  )
    date        = models.DateTimeField( _('date of start') )
    date_end    = models.DateTimeField(
                      _('date of end')
                    , blank = True
                    , null = True
                  )
    public      = models.BooleanField(
                      _('public')
                    , default = False
                    , help_text = _('publication is accessible to the public')
                  )
    meta        = models.TextField (
                      _('meta')
                    , blank = True
                    , null = True
                  )
    canceled    = models.BooleanField( _('canceled'), default = False )


    def testify (self):
        parent = self.parent
        self.parent.testify()
        self.parent.date = self.date
        return self.parent


    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')


