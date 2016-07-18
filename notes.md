
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
    - update documentation:
        - cms.script
        - cms.exposure; make it right, see nomenclature, + docstring
        - cms.actions;
    - admin cms
        -> sections/actions and django decorator?
        -> enhance calendar with possible actions?

- website:
    - article list with the focus
    - player:
        - mixcloud
        - remove from playing playlist -> stop
    - date_by_list:
        - sections' url

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


