
# TODO:
- general:
    - timezone shit
    - translation

- programs:
    - schedule changes -> update later diffusions according to the new schedule
    - stream disable -> remote control on liquidsoap
    - tests:
        - sound_monitor

- liquidsoap:
    - models to template -> note
    - tests:
        - monitor
        - check when a played sound has a temp blank
        - config generation and sound diffusion

- cms:
    - empty content -> empty string
    - update documentation:
        - cms.script
        - cms.exposure; make it right, see nomenclature, + docstring
    - admin cms
    - sections:
        - article list with the focus
            -> set html attribute based on values that are public

- website:
    - render schedule does not get the correct list
        -> postlistview has not the same queryset as website/sections/schedule
    - diffusions:
        - filter sounds for undiffused diffusions
        - print sounds of diffusions
        - print program's name in lists
    - player:
        - mixcloud
        - seek bar
    - list of played diffusions and tracks when non-stop;

# Later todo
- sounds monitor: max_size of path, take in account
- logs: archive functionnality
- track stats for diffusions
- debug/prod configuration
- player support diffusions with multiple archive files
- view as grid



