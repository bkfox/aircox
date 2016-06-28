{% comment %}
Base configuration file to configure a station on liquidsoap.

A Station is composed of multiple streams, that includes:
- controller.dealer: used to play scheduled programs;
- controller.streams: streams configured to play random sounds;

# Interactive elements:
An interactive element is accessible to the people, in order to:
- get metadata
- skip the current sound
- enable/disable it, only for the dealer

- {controller.id}: the station itself
- {controller.id}_streams: all the streams of a controller
- {source.id}: for each stream of a controller + dealer


# Element of the context
We use theses elements from the template's context:
- controller: controller describing the station itself
- settings: global settings

# Overwrite the template
It is possible to overwrite the template, there are blocks at different
position in order to do it. Keep in mind that you might want to avoid to
put station specific configuration in the template itself.
{% endcomment %}


{% comment %}
An interactive source is a source that:
- is skippable through the given id on external interfaces
- store metadata
{% endcomment %}
def interactive_source (id, s) =
    s = store_metadata(id=id, size=1, s)
    add_skip_command(s)
    s
end

{% comment %}
a stream is a source that:
- is a playlist on random mode (playlist object accessible at {id}_playlist
- is interactive
{% endcomment %}
def stream (id, file) =
    #s = playlist(id = '#{id}_playlist', mode = "random",
    #             file)
    s = playlist(id = '#{id}_playlist', mode = "random", file)
    interactive_source(id, s)
end

{% block extra_funcs %}
{% endblock %}
\
{# config #}
set("server.socket", true)
set("server.socket.path", "{{ controller.socket_path }}")
{% for key, value in settings.AIRCOX_LIQUIDSOAP_SET.items %}
set("{{ key|safe }}", {{ value|safe }})
{% endfor %}

{% block extra_config %}
{% endblock %}


{# station #}
{{ controller.id }} = interactive_source (
    "{{ controller.id }}",
    fallback(track_sensitive = false, [
        {# dealer #}
        {% with source=controller.dealer %}
        {% if source %}
        at(interactive.bool('{{ source.id }}_on', false),
            interactive_source('{{ source.id }}', playlist.once(
                reload_mode='watch',
                "{{ source.path }}",
            ))
        ),
        {% endif %}
        {% endwith %}

        {# streams #}
        interactive_source("{{ controller.id }}_streams", rotate([
            {% for source in controller.streams.values %}
            {% with info=source.stream_info %}
                    {% if info.delay %}
                delay({{ info.delay }}., stream("{{ source.id }}", "{{ source.path }}")),
                    {% elif info.begin and info.end %}
                at({ {{info.begin}}-{{info.end}} }, stream("{{ source.id }}", "{{ source.path }}")),
                    {% endif %}
            {% endwith %}
            {% endfor %}

            {% for source in controller.streams.values %}
                {% if not source.stream_info %}
            stream("{{ source.id }}", "{{ source.path }}"),
                {% endif %}
            {% endfor %}
        ])),

        {# fallback #}
        {% if controller.station.fallback %}
            single("{{ controller.station.fallback }}"),
        {% else %}
            blank(id="scheize_blank", duration=0.1),
        {% endif %}
    ])
)
\

{% block outputs %}
{% for output in controller.outputs %}
output.{{ output.get_type_display }}(
   {{ controller.id }}
    {% if controller.settings %},
    {{ controller.settings }}
    {% endif %}
)
{% endfor %}

{% block extra_output %}
{% endblock %}
{% endfor %}

