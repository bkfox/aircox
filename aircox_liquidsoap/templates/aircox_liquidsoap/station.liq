{% comment %}
A station has multiple sources:
- dealer: a controlled playlist playing once each track, that reloads on file
    change. This is used for scheduled sounds.
- streams: a rotate source with all playlists
- single: security song
{% endcomment %}
{% with name=station.name streams=station.streams %}
def make_station_{{ name }} () = \
    {# dealer #}
    dealer = interactive_source('{{ name }}_dealer', playlist.once( \
        reload_mode='watch', \
        '/tmp/dealer.m3u', \
    )) \
    \
    dealer_on = interactive.bool("{{ name }}_dealer_on", false) \
    \
    {# streams #}
    streams = interactive_source("streams", rotate([ \
    {% for stream in streams %}
    {% if stream.delay %}
        delay({{ stream.delay }}., stream("{{ name }}_{{ stream.name }}", "{{ stream.file }}")), \
    {% endif %}
    {% endfor %}

        switch([ \
    {% for stream in streams %}
    {% if stream.begin and stream.end %}
            ({ stream.begin, stream.end }, stream("{{ name }}_{{ stream.name }}", "{{ stream.file }}")), \
    {% endif %}
    {% endfor %}
        ]), \

    {% for stream in streams %}
    {% if not stream.delay %}
    {% if not stream.begin or not stream.end %}
        stream("{{ name }}_{{ stream.name }}", "{{ stream.file }}"), \
    {% endif %}
    {% endif %}
    {% endfor %}
    ])) \
    \
    {# station #}
    interactive_source ( \
        "{{ name }}", \
        fallback(track_sensitive = false, [ \
            at(dealer_on, dealer), \
        {% if station.fallback %}
            streams, \
            single("{{ station.fallback }}") \
        {% else %}
            mksafe(streams) \
        {% endif %}
        ]) \
    ) \
end \
{% endwith %}

