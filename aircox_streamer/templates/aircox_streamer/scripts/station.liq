{% comment %}
Base liquidsoap station configuration.


[stream] +--> streams ---+---> station
                         |
              dealer  ---'

{% endcomment %}

{% block functions %}
{# Seek function #}
def seek(source, t) =
  t = float_of_string(default=0.,t)
  ret = source.seek(source,t)
  log("seek #{ret} seconds.")
  "#{ret}"
end

{# Transition to live sources #}
def to_live(stream, live)
  stream = fade.final(duration=2., type='log', stream)
  live = fade.initial(duration=2., type='log', live)
  add(normalize=false, [stream,live])
end

{# Transition to stream sources #}
def to_stream(live, stream)
  source.skip(stream)
  add(normalize=false, [live,stream])
end


{% comment %}
An interactive source is a source that:
- is skippable through the given id on external interfaces
- is seekable through the given id and amount of seconds on e.i.
- store metadata
{% endcomment %}
def interactive (id, s) =
    server.register(namespace=id,
                    description="Seek to a relative position",
                    usage="seek <duration>",
                    "seek", fun (x) ->  begin seek(s, x) end)
    server.register(namespace=id,
                    description="Get source's track remaining time",
                    usage="remaining",
                    "remaining", fun (_) ->  begin json_of(source.remaining(s)) end)

    s = store_metadata(id=id, size=1, s)
    add_skip_command(s)
    s
end

{% comment %}
A stream is an interactive playlist
{% endcomment %}
def stream (id, file) =
    s = playlist(mode = "random", reload_mode='watch', file)
    interactive(id, s)
end
{% endblock %}


{% block config %}
set("server.socket", true)
set("server.socket.path", "{{ streamer.socket_path }}")
set("log.file.path", "{{ station.path }}/liquidsoap.log")
{% for key, value in settings.AIRCOX_LIQUIDSOAP_SET.items %}
set("{{ key|safe }}", {{ value|safe }})
{% endfor %}
{% endblock %}

{% block config_extras %}
{% endblock %}


{% block sources %}
{% with source=streamer.dealer %}
live = interactive('{{ source.id }}',
    request.queue(id="{{ source.id }}_queue")
)
{% endwith %}


streams = rotate(id="streams", [
    {% for source in streamer.sources %}
    {% if source != streamer.dealer %}
    {% with stream=source.stream %}
        {% if stream.delay %}
        delay({{ stream.delay }}.,
              stream("{{ source.id }}", "{{ source.path }}")),
        {% elif stream.begin and stream.end %}
        at({ {{stream.begin}}-{{stream.end}} },
           stream("{{ source.id }}", "{{ source.path }}")),
        {% else %}
        stream("{{ source.id }}", "{{ source.path }}"),
        {% endif %}
    {% endwith %}
    {% endif %}
    {% endfor %}
])

{% endblock %}


{% block station %}
{{ streamer.id }} = interactive (
    "{{ streamer.id }}",
    fallback([
        live,
        streams,
        blank(id="blank", duration=0.1)
    ], track_sensitive=false, transitions=[to_live,to_stream])
)
{% endblock %}


{% block outputs %}
{% for output in streamer.outputs %}
output.{{ output.get_type_display }}(
    {% if output.settings %}
    {{ output.settings|safe }},
    {% endif %}
    {{ streamer.id }}
)
{% endfor %}
{% endblock %}


