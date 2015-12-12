{# Context: #}
{# - controller: controller used to generate the current file #}
{# - settings: global settings #}

def interactive_source (id, s) = \
    s = store_metadata(id=id, size=1, s) \
    add_skip_command(s) \
    s \
end \
\
def stream (id, file) = \
    s = playlist(id = '#{id}_playlist', mode = "random", \
                 reload_mode='watch', file) \
    interactive_source(id, s) \
end \
\
{# Config #}
set("server.socket", true) \
set("server.socket.path", {{ controller.socket_path }}) \
{% for key, value in settings.AIRCOX_LIQUIDSOAP_SET.items %}
set("{{ key|safe }}", {{ value|safe }}) \
{% endfor %}
\
{# station #}
{{ controller.id }} = interactive_source ( \
    "{{ controller.id }}", \
    fallback(track_sensitive = false, [ \
        {# dealer #}
        {% with source=controller.dealer %}
        {% if source %}
        at(interactive.bool('{{ source.id }}_on', false), \
            interactive_source('{{ source.id }}', playlist.once( \
                reload_mode='watch', \
                "{{ source.path }}", \
            )) \
        ), \
        {% endif %}
        {% endwith %}

        {# streams #}
        interactive_source("{{ controller.id }}_streams", rotate([ \
            {% for source in controller.streams.values %}
            {% with info=source.stream_info %}
                {% if info.delay %}
            delay({{ info.delay }}., stream("{{ source.id }}", "{{ source.path }}")), \
                {% elif info.begin and info.end %}
            at({ {{info.begin}}-{{info.end}} }, stream("{{ source.id }}", "{{ source.path }}")), \
                {% endif %}
            {% endwith %}
            {% endfor %}

            {% for source in controller.streams.values %}
                {% if not source.stream_info %}
            stream("{{ source.id }}", "{{ source.path }}"), \
                {% endif %}
            {% endfor %}
        ])), \

        {# fallback #}
        {% if controller.station.fallback %}
            single("{{ controller.station.fallback }}"), \
        {% else %}
            blank(), \
        {% endif %}
    ]) \
) \
\
{% for output in controller.outputs %}
output.{{ output.get_type_display }}( \
   {{ controller.id }}
    {% if controller.settings %}, \
    {{ controller.settings }}
    {% endif %}
) \
{% endfor %}

