This file is used as a reminder, can be used as crappy documentation too.

- player
- monitor interface
- statistics interface
- traduction
- hot reload

Améliorations:
- calendar dashboard
- accessibilité
- player: playlist


# for the 1.0
- logs:
    - do not add track if between two consecutive diffusions
- run tests:
    - streamer: dealer & streams hours (to localtime)
    x diffusions: update & check algorithms
    x check in templates
    x diffusion page date info
- streamer:
    - restart running streamer on demand
    - add restart button for the streamer
    \--> rewrite streamer for client-server controller
    \--> move liquidsoap control on commands/streamer.py
- cms:
    x button to select the current station
    - section's title: format with current page info e.g. "The diffusions of {program.name}" -- perhaps use pass **context
    - section exclude: exclude a section for a given page type
    - category page
    - for timetable, logs, etc. make station optional
    - django's message css displayed on pages when element is modified (remove bullet)
    - articles preview in different format


# conventions
## coding style
* name of classes relative to a class:
    - metaclass: `class_name + 'Meta'`
    - base classes: `class_name + 'Base'`

* import and naming:
    - the imported "models" file in the same application is named "models"
    - the imported "models" file from another application is named with the application's name
    - to avoid conflict:
        - django's settings can be named "main_settings"

## aircox.cms
* icons: cropped to 32x32
* cover in list items: cropped 64x64



# To discuss / To think
- aircox_cms.signals: handle renaming of the program if the article's title has
    not been changed -> need to cache of the title at __init__
- ensure per station website for all generated publications
- aircox_cms: remove "station" fields when it is possible in the pages & sections


# Long term TODO
programs:
    - sounds monitor: max_size of path, take in account
    - archives can be set afterwards for rerun, so check must be done
        at the same time we monitor
    - logs: archive functionnality
    - tools:
        - track stats for diffusions

cms:
    - player support diffusions with multiple archive files
    - comments -> remove/edit by the author

# Timezone shit:

# Instance's TODO
- menu_top .sections:
    - display inline block
    - search on the right
- lists > items style
- logo: url
- comments / more info (perhaps using the thing like the player)
- footer url to aircox's repo + admin
- styling cal (a.today colored)

- init of post related models
    -> date is not formatted
    -> missing image?



