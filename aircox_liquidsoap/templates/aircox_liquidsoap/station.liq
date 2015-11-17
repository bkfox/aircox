{% comment %}
A station has multiple sources:
- dealer: a controlled playlist playing once each track, that reloads on file
    change. This is used for scheduled sounds.
- streams: a rotate source with all playlists
- single: security song
{% endcomment %}
def make_station_{{ controller.id }} () = \
    {# dealer #}
    {% with source=controller.dealer %}
    {% if source %}
    dealer = interactive_source('{{ source.id }}', playlist.once( \
        reload_mode='watch', \
        "{{ source.path }}", \
    )) \
    \
    dealer_on = interactive.bool("{{ source.id }}_on", false) \
    {% endif %}
    {% endwith %}
    \
    {# streams #}
    streams = interactive_source("streams", rotate([ \
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
    ])) \
    \
    {# station #}
    interactive_source ( \
        "{{ controller.id }}", \
        fallback(track_sensitive = false, [ \
            at(dealer_on, dealer), \
            streams, \
        {% if controller.station.fallback %}
            single("{{ controller.station.fallback }}"), \
        {% else %}
            blank(), \
        {% endif %}
        ]) \
    ) \
end \

