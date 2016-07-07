from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.cms.actions import Action
import aircox.website.utils as utils

class AddToPlaylist(Action):
    """
    Remember a sound and add it into the default playlist. The given
    object can be:
    - a Diffusion post
    - a programs.Sound instance
    - an object with an attribute 'sound' used to generate the code
    """
    id = 'sound.add'
    symbol = '☰'
    title = _('add to the playlist')
    code = """
    function(sound, item) {
        Player.playlist.add(sound);
        item.parentNode.removeChild(item)
    }
    """

    @classmethod
    def make_for_diffusions(cl, request, object):
        from aircox.website.sections import Player
        if object.related.end > tz.make_aware(tz.datetime.now()):
            return

        archives = object.related.get_archives()
        if not archives:
            return False

        sound = Player.make_sound(object, archives[0])
        return cl.to_str(object, **sound)

    @classmethod
    def make_for_sound(cl, request, object):
        from aircox.website.sections import Player
        sound = Player.make_sound(None, object)
        return cl.to_str(object, **sound)

    @classmethod
    def test(cl, request, object, in_list):
        from aircox.programs.models import Sound
        from aircox.website.models import Diffusion

        print(object)
        if not in_list:
            return False

        if issubclass(type(object), Diffusion):
            return cl.make_for_diffusions(request, object)
        if issubclass(type(object), Sound):
            return cl.make_for_sound(request, object)
        if hasattr(object, 'sound') and object.sound:
            return cl.make_for_sound(request, object.sound)

class Play(AddToPlaylist):
    """
    Play a sound
    """
    id = 'sound.play'
    symbol = '▶'
    title = _('listen')
    code = """
    function(sound) {
        sound = Player.playlist.add(sound);
        Player.select_playlist(Player.playlist);
        Player.select(sound, true);
    }
        """


