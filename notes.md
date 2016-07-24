This file is used as a reminder, can be used as crappy documentation too.

# conventions
## coding style
* name of classes relative to a class:
    - metaclass: `class_name + 'Meta'`
    - base classes: `class_name + 'Base'`

## aircox.cms
* icons: cropped to 32x32
* cover in list items: cropped 64x64



# TODO:
- general:
    - timezone shit
    - translation

- programs:
    - schedule changes -> update later diffusions according to the new schedule
    - users
    - tests:
        - sound_monitor
        - import_playlist

- controllers :
    - models to template -> note
    - streamed program disable -> remote control on liquidsoap
    - tests:
        - monitor
        - check when a played sound has a temp blank
        - config generation and sound diffusion

- cms:
    - command to sync programs with cms's
    - player:
        - mixcloud
        - remove from playing playlist -> stop
    - filter choices on DiffusionPage and ProgramPage related objects

# Long term TODO
- automatic cancel of passed diffusion based on logs?
    - archives can be set afterwards for rerun, so check must be done
        at the same time we monitor
- sounds monitor: max_size of path, take in account
- logs: archive functionnality
- track stats for diffusions
- debug/prod configuration
- player support diffusions with multiple archive files
- view as grid
- actions -> noscript case, think of accessibility
- comments -> remove/edit by the author
- integrate logs for tracks + in on air
- rename controllers.Station into controllers.Streamer -> keep Station for sth else


