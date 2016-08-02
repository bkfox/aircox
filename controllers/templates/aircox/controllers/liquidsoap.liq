{% comment %}
TODO: update doc
Base configuration file to configure a station on liquidsoap.

# Interactive elements:
An interactive element is accessible to the people, in order to:
- get metadata
- skip the current sound
- enable/disable it

# Element of the context
We use theses elements from the template's context:
- controller: controller describing the station itself
- settings: global settings

# Overwrite the template
It is possible to overwrite the template, there are blocks at different
position in order to do it. Keep in mind that you might want to avoid to
put station specific configuration in the template itself.
{% endcomment %}


{% block functions %}
{% comment %}
An interactive source is a source that:
- is skippable through the given id on external interfaces
- can be disabled
- store metadata
{% endcomment %}
def interactive_source (id, s, ~active=true, ~disable_switch=false) =
    s = store_metadata(id=id, size=1, s)
    add_skip_command(s)
    if disable_switch then
        s
    else
        at(interactive.bool('#{id}_active', active), s)
    end
end

{% comment %}
A stream is a source that:
- is a playlist on random mode (playlist object accessible at {id}_playlist
- is interactive
{% endcomment %}
def stream (id, file) =
    s = playlist(id = '#{id}_playlist', mode = "random", file)
    interactive_source(id, s)
end
{% endblock %}

{% block functions_extras %}
{% endblock %}


{% block config %}
set("server.socket", true)
set("server.socket.path", "{{ station.controller.socket_path }}")
set("log.file.path", "{{ station.controller.station.path }}/liquidsoap.log")
{% for key, value in settings.AIRCOX_LIQUIDSOAP_SET.items %}
set("{{ key|safe }}", {{ value|safe }})
{% endfor %}
{% endblock %}

{% block config_extras %}
{% endblock %}


{% block sources %}
live = fallback([
    {% for source in station.file_sources %}
    {% with controller=source.controller %}
    interactive_source(
        '{{ source.id_ }}', single("{{ source.url }}"), active=false
    ),
    {% endwith %}
    {% endfor %}

    {% with source=station.dealer controller=station.dealer.controller %}
    interactive_source('{{ source.id_ }}',
        playlist.once(reload_mode='watch', "{{ controller.path }}"),
        active=false
    ),
    {% endwith %}
])


stream = fallback([
    rotate([
        {% for source in station.stream_sources %}
        {% with controller=source.controller stream=source.controller.stream %}
            {% if stream.delay %}
            delay({{ stream.delay }}.,
                  stream("{{ source.id_ }}", "{{ controller.path }}")),
            {% elif stream.begin and stream.end %}
            at({ {{stream.begin}}-{{stream.end}} },
               stream("{{ source.id_ }}", "{{ controller.path }}")),
            {% elif not stream %}
            stream("{{ source.id_ }}", "{{ controller.path }}"),
            {% endif %}
        {% endwith %}
        {% endfor %}
    ]),

    {% for source in station.fallback_sources %}
    {% with controller=source.controller %}
    single("{{ source.value }}"),
    {% endwith %}
    {% endfor %}

    blank(id="blank_fallback", duration=0.1),
])

{% endblock %}

{% block sources_extras %}
{% endblock %}


def to_live(stream,live)
  stream = fade.final(duration=2., type='log', stream)
  live = fade.initial(duration=2., type='log', live)
  add(normalize=false, [stream,live])
end

def to_stream(live,stream)
  source.skip(stream)
  add(normalize=false, [live,stream])
end


{% block station %}
{{ station.id_ }} = interactive_source (
    "{{ station.id_ }}",
    fallback(
        track_sensitive=false,
        transitions=[to_live,to_stream],
        [ live, stream ]
    ),
    disable_switch=true
)
{% endblock %}


{% block station_extras %}
{% endblock %}


{% block outputs %}
{% for output in station.outputs %}
output.{{ output.get_type_display }}(
    {{ station.id_ }},
    {% if controller.settings %},
    {{ output.settings }}
    {% endif %}
)
{% endfor %}
{% endblock %}

{% block output_extras %}
{% endblock %}

