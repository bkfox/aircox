import datetime

from django.utils.translation import ugettext as _
from django.utils import timezone as tz

from ..models import Diffusion, Log, Page
from .page import PageListView

class HomeView(PageListView):
    template_name = 'aircox/home.html'
    model = Page
    queryset = Page.objects.select_subclasses()
    paginate_by = 10
    list_count = 40
    logs_count = 5
    has_filters = False

    def get_logs(self):
        today = datetime.date.today()
        logs = Log.objects.on_air().today(today).filter(track__isnull=False)
        diffs = Diffusion.objects.on_air().today(today)
        return Log.merge_diffusions(logs, diffs, self.logs_count)

    def get_sidebar_queryset(self):
        today = datetime.date.today()
        return Diffusion.objects.on_air().today(today)

    def get_top_diffs(self):
        now = tz.now()
        current_diff = Diffusion.objects.on_air().now(now).first()
        next_diffs = Diffusion.objects.on_air().after(now)
        if current_diff:
            diffs = [current_diff] + list(next_diffs.exclude(pk=current_diff.pk)[:2])
        else:
            diffs = next_diffs[:3]
        return diffs

    def get_context_data(self, **kwargs):
        kwargs['logs'] = self.get_logs()
        kwargs['top_diffs'] = self.get_top_diffs()
        return super().get_context_data(**kwargs)



