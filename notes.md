
# TODO:
- general:
    - timezone shit
    - translation

- programs:
    - schedule changes -> update later diffusions according to the new schedule
    - stream disable -> remote control on liquidsoap
    - users
    - tests:
        - sound_monitor

- liquidsoap:
    - models to template -> note
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
    - sections id generator

- website:
    - diffusions:
        - print program's name in lists / clean up that thing also a bit
    - article list with the focus
    - player:
        - mixcloud
        - seek bar + timer
        - remove from playing playlist -> stop
    - list of played diffusions and tracks when non-stop;

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



