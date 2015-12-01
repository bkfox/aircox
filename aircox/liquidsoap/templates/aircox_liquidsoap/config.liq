{# Utilities #}
def interactive_source (id, s, ) = \
    s = store_metadata(id=id, size=1, s) \
    add_skip_command(s) \
    s \
end \
\
def stream (id, file) = \
    s = playlist(id = '#{id}_playlist', mode = "random", file) \
    interactive_source(id, s) \
end \
\
{# Config #}
set("server.socket", true) \
set("server.socket.path", "{{ settings.AIRCOX_LIQUIDSOAP_SOCKET }}") \
{% for key, value in settings.AIRCOX_LIQUIDSOAP_SET.items %}
set("{{ key|safe }}", {{ value|safe }}) \
{% endfor %}
\
\
{% for controller in monitor.controllers.values %}
{% include 'aircox_liquidsoap/station.liq' %} \
{{ controller.id }} = make_station_{{ controller.id }}() \
output.alsa({{ controller.id }}) \
{% endfor %}

