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
from sortedm2m.fields                       import SortedManyToManyField

import programs.settings                    as settings



# Frequency for schedules. Basically, it is a mask of bits where each bit is a
# week. Bits > rank 5 are used for special schedules.
# Important: the first week is always the first week where the weekday of the
# schedule is present.
Frequency = {
    'ponctual':         0b000000
  , 'first':            0b000001
  , 'second':           0b000010
  , 'third':            0b000100
  , 'fourth':           0b001000
  , 'last':             0b010000
  , 'first and third':  0b000101
  , 'second and fourth': 0b001010
  , 'every':            0b011111
  , 'one on two':       0b100000
}



# Translators: html safe values
ugettext_lazy('ponctual')
ugettext_lazy('every')
ugettext_lazy('first')
ugettext_lazy('second')
ugettext_lazy('third')
ugettext_lazy('fourth')
ugettext_lazy('first and third')
ugettext_lazy('second and fourth')
ugettext_lazy('one on two')


DiffusionType = {
    'diffuse':  0x01   # the diffusion is planified or done
  , 'cancel':   0x03   # the diffusion has been canceled from grid; useful to give
                        # the info to the users
  , 'stop':     0x04   # the diffusion been arbitrary stopped (non-stop or not)
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
    private     = models.BooleanField(
                      _('private')
                    , default = False
                    , help_text = _('publication is private')
                  )
    # FIXME: add a field to specify if the element should be listed or not
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
    def get_upload_path (self, filename):
        if self.parent and self.parent.parent:
            path = self.parent.parent.path
        else:
            path = settings.AIRCOX_SOUNDFILE_DEFAULT_DIR
        return os.path.join(path, filename)


    parent      = models.ForeignKey(
                      'Episode'
                    , verbose_name = _('episode')
                    , blank = True
                    , null = True
                  )
    file        = models.FileField( #FIXME: filefield
                      _('file')
                    , upload_to = get_upload_path
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


    def get_mtime (self):
        """
        Get the last modification date from file
        """
        mtime = os.stat(self.file.path).st_mtime
        mtime = timezone.datetime.fromtimestamp(mtime)
        return timezone.make_aware(mtime, timezone.get_current_timezone())


    def save (self, *args, **kwargs):
        if not self.pk:
            self.date = self.get_mtime()
        super(SoundFile, self).save(*args, **kwargs)


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
    rerun       = models.ForeignKey(
                    'self'
                  , blank = True
                  , null = True
                  , help_text = "Schedule of a rerun"
                  )


    def match (self, date = None, check_time = False):
        """
        Return True if the given datetime matches the schedule
        """
        if not date:
            date = timezone.datetime.today()

        if self.date.weekday() == date.weekday() and self.match_week(date):
            return (check_time and self.date.time() == date.date.time()) or True
        return False


    def match_week (self, date = None):
        """
        Return True if the given week number matches the schedule, False
        otherwise.
        If the schedule is ponctual, return None.
        """
        if not date:
            date = timezone.datetime.today()

        if self.frequency == Frequency['ponctual']:
            return None

        if self.frequency == Frequency['one on two']:
            week = date.isocalendar()[1]
            return (week % 2) == (self.date.isocalendar()[1] % 2)

        first_of_month = timezone.datetime.date(date.year, date.month, 1)
        week = date.isocalendar()[1] - first_of_month.isocalendar()[1]

        # weeks of month
        if week == 4:
            # fifth week: return if for every week
            return self.frequency == 0b1111
        return (self.frequency & (0b0001 << week) > 0)


    def normalize (self, date):
        """
        Set the time of a datetime to the schedule's one
        """
        return date.replace( hour = self.date.hour
                           , minute = self.date.minute )


    def dates_of_month (self, date = None):
        """
        Return a list with all matching dates of the month of the given
        date (= today).
        """
        if self.frequency == Frequency['ponctual']:
            return None

        if not date:
            date = timezone.datetime.today()

        date = timezone.datetime( year = date.year
                                 , month = date.month
                                 , day = 1 )
        wday = self.date.weekday()
        fwday = date.weekday()

        # move date to the date weekday of the schedule
        # check on SO#3284452 for the formula
        date += timezone.timedelta(
                    days = (7 if fwday > wday else 0) - fwday + wday
                 )
        fwday = date.weekday()

        # special frequency case
        weeks = self.frequency
        if self.frequency == Frequency['last']:
            date += timezone.timedelta(month = 1, days = -7)
            return self.normalize([date])
        if weeks == Frequency['one on two']:
            # if both week are the same, then the date week of the month
            # matches. Note: wday % 2 + fwday % 2 => (wday + fwday) % 2
            fweek = date.isocalendar()[1]
            week = self.date.isocalendar()[1]
            weeks = 0b010101 if not (fweek + week) % 2 else 0b001010

        dates = []
        for week in range(0,5):
            # NB: there can be five weeks in a month
            if not weeks & (0b1 << week):
                continue

            wdate = date + timezone.timedelta(days = week * 7)
            if wdate.month == date.month:
                dates.append(self.normalize(wdate))
        return dates


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

    @property
    def path (self):
        return os.path.join( settings.AIRCOX_PROGRAMS_DIR
                           , slugify(self.title + '_' + str(self.id))
                           )


    def find_schedules (self, date):
        """
        Return schedules that match a given date
        """
        schedules = Schedule.objects.filter(parent = self)
        r = []
        for schedule in schedules:
            if schedule.match_date(date):
                r.append(schedule)
        return r


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
    # FIXME: ponctual replays?
    parent      = models.ForeignKey(
                      Program
                    , verbose_name = _('parent')
                  )
    tracks      = SortedManyToManyField(
                      Track
                    , verbose_name = _('tracks')
                  )


    class Meta:
        verbose_name = _('Episode')
        verbose_name_plural = _('Episodes')



class Diffusion (Model):
    """
    Diffusion logs and planifications.

    A diffusion is:
    - scheduled: when it has been generated following programs' Schedule
    - planified: when it has been generated manually/ponctually or scheduled
    """
    parent      = models.ForeignKey (
                      Episode
                    , blank = True
                    , null = True
                  )
    program     = models.ForeignKey (
                      Program
                  )
    type        = models.SmallIntegerField(
                      verbose_name = _('type')
                    , choices = [ (y, x) for x,y in DiffusionType.items() ]
                  )
    date        = models.DateTimeField( _('date of diffusion start') )
    stream      = models.SmallIntegerField(
                      verbose_name = _('stream')
                    , default = 0
                    , help_text = 'stream id on which the diffusion happens'
                  )
    scheduled   = models.BooleanField(
                      verbose_name = _('automated')
                    , default = False
                    , help_text = 'diffusion generated automatically'
                  )

    def save (self, *args, **kwargs):
        if self.parent:
            self.program = self.parent.parent
        super(Diffusion, self).save(*args, **kwargs)


    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')


