import os

# django
from django.db                              import models
from django.contrib.auth.models             import User
from django.template.defaultfilters         import slugify
from django.contrib.contenttypes.fields     import GenericForeignKey
from django.contrib.contenttypes.models     import ContentType
from django.utils.translation               import ugettext as _, ugettext_lazy
from django.utils                           import timezone
from django.utils.html                      import strip_tags

# extensions
from taggit.managers                        import TaggableManager

import programs.settings                    as settings



Frequency = {
    'ponctual':          0b000000
  , 'every week':        0b001111
  , 'first week':        0b000001
  , 'second week':       0b000010
  , 'third week':        0b000100
  , 'fourth week':       0b001000
  , 'first and third':   0b000101
  , 'second and fourth': 0b001010
  , 'one week on two':   0b010010
    #'uneven week':         0b100000
    # TODO 'every day':     0b110000
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


EventType = {
    'play':     0x02    # the sound is playing / planified to play
  , 'cancel':   0x03    # the sound has been canceled from grid; useful to give
                        # the info to the users
  , 'stop':     0x04    # the sound has been arbitrary stopped (non-stop or not)
  , 'non-stop': 0x05    # the sound has been played as non-stop
#, 'streaming'
}



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
                    , default = timezone.datetime.now
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
    file        = models.FileField( #FIXME: filefield
                      _('file')
                    , upload_to = lambda i, f: SoundFile.__upload_path(i,f)
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
    embed       = models.TextField(
                      _('embed HTML code from external website')
                    , blank = True
                    , null = True
                    , help_text = _('if set, consider the sound podcastable from there')
                  )
    removed     = models.BooleanField(
                      default = False
                    , help_text = _('this sound has been removed from filesystem')
                  )


    def __upload_path (self, filename):
        if self.parent and self.parent.parent:
            path = self.parent.parent.path
        else:
            path = settings.AIRCOX_SOUNDFILE_DEFAULT_DIR
        return os.path.join(path, filename)


    def __str__ (self):
        return str(self.id) + ': ' + self.file.name


    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')


class Schedule (Model):
    parent      = models.ForeignKey( 'Program', blank = True, null = True )
    date        = models.DateTimeField(_('start'))
    duration    = models.TimeField(
                      _('duration')
                    , blank = True
                    , null = True
                  )
    frequency   = models.SmallIntegerField(
                      _('frequency')
                    , choices = [ (y, x) for x,y in Frequency.items() ]
                  )
    rerun       = models.BooleanField(_('rerun'), default = False)


    def match_date (self, at = timezone.datetime.today()):
        """
        Return True if the given datetime matches the schedule
        """
        if self.date.weekday() == at.weekday() and self.match_week(date):
            return self.date.time() == at.date.time()
        return False


    def match_week (self, at = timezone.datetime.today()):
        """
        Return True if the given week number matches the schedule, False
        otherwise.
        If the schedule is ponctual, return None.
        """
        if self.frequency == Frequency['ponctual']:
            return None

        if self.frequency == Frequency['one week on two']:
            week = at.isocalendar()[1]
            return (week % 2) == (self.date.isocalendar()[1] % 2)

        first_of_month = timezone.datetime.date(at.year, at.month, 1)
        week = at.isocalendar()[1] - first_of_month.isocalendar()[1]

        # weeks of month
        if week == 4:
            # fifth week: return if for every week
            return self.frequency == 0b1111
        return (self.frequency & (0b0001 << week) > 0)


    def next_date (self, at = timezone.datetime.today()):
        if self.frequency == Frequency['ponctual']:
            return None

        # first day of the week
        date = at - timezone.timedelta( days = at.weekday() )

        # for the next five week, we look for a matching week.
        # when found, add the number of day since de start of the
        # we need to test if the result is >= at
        for i in range(0,5):
            if self.match_week(date):
                date_ = date + timezone.timedelta( days = self.date.weekday() )
                if date_ >= at:
                    # we don't want past events
                    return timezone.datetime(date_.year, date_.month, date_.day,
                                                self.date.hour, self.date.minute)
            date += timezone.timedelta( days = 7 )
        else:
            return None


    def next_dates (self, at = timezone.datetime.today(), n = 52):
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
            at = res[-1] + timezone.timedelta(days = 1)

        return res


    #def to_string(self):
    #    s = ugettext_lazy( RFrequency[self.frequency] )
    #    if self.rerun:
    #        return s + ' (' + _('rerun') + ')'
    #    return s

    def __str__ (self):
        frequency = [ x for x,y in Frequency.items() if y == self.frequency ]
        return self.parent.title + ': ' + frequency[0]


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
    non_stop    = models.SmallIntegerField(
                      _('non-stop priority')
                    , help_text = _('this program can be used as non-stop')
                    , default = -1
                  )

    @property
    def path(self):
        return os.path.join( settings.AIRCOX_PROGRAMS_DIR
                           , slugify(self.title + '_' + str(self.id))
                           )


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
    Event logs and planification of a sound file
    """
    sound       = models.ForeignKey (
                      SoundFile
                    , verbose_name = _('sound file')
                  )
    type        = models.SmallIntegerField(
                      _('type')
                    , choices = [ (y, x) for x,y in EventType.items() ]
                  )
    date        = models.DateTimeField( _('date of event start') )
    meta        = models.TextField (
                      _('meta')
                    , blank = True
                    , null = True
                  )


    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')


