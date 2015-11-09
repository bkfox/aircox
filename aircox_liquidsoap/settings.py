
from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


ensure('AIRCOX_LIQUIDSOAP_SOCKET', '/tmp/liquidsoap.sock')

# dict of values to set (do not forget to escape chars)
ensure('AIRCOX_LIQUIDSOAP_SET', {
    'log.file.path': '"/tmp/liquidsoap.log"',
})

# security source: used when no source are available
ensure('AIRCOX_LIQUIDSOAP_SECURITY_SOURCE', '/media/data/musique/creation/Mega Combi/MegaCombi241-PT134-24062015_Comme_des_lyca_ens.mp3')

# start the server on monitor if not present
ensure('AIRCOX_LIQUIDSOAP_AUTOSTART', True)

# output directory for the generated files
ensure('AIRCOX_LIQUIDSOAP_MEDIA', '/tmp')


