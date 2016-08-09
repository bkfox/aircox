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
    - input stream
    - streamed program disable -> remote control on liquidsoap
    - tests:
        - monitor
        - config generation and sound diffusion

- cms:
    - player:
        - mixcloud
        - remove from playing playlist -> stop
    - filter choices on DiffusionPage and ProgramPage related objects


# Long term TODO
- debug/prod configuration

programs:
    - sounds monitor: max_size of path, take in account

controllers:
    - automatic cancel of passed diffusion based on logs?
        - archives can be set afterwards for rerun, so check must be done
            at the same time we monitor
    - logs: archive functionnality
    - tools:
        - track stats for diffusions
    - rename controllers.Station into controllers.Streamer -> keep Station for sth else

cms:
    - player support diffusions with multiple archive files
    - comments -> remove/edit by the author


