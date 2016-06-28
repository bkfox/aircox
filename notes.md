- sounds monitor: max_size of path, take in account
- logs: archive functionnality + track stats for diffusions
- debug/prod configuration

# TODO:
- general:
    - timezone shit
    - translation

- programs:
    - tests:
        - sound_monitor

- liquidsoap:
    - models to template -> note
    - tests:
        - monitor
        - check when a played sound has a temp blank
        - config generation and sound diffusion

- cms:
    - switch to abstract class and remove qcombine (or keep it smw else)?
    - empty content -> empty string
    - update documentation:
        - cms.script
        - cms.exposure; make it right, see nomenclature, + docstring
    - admin cms
    - sections:
        - calendar
        - article list with the focus
            -> set html attribute based on values that are public

- website:
    - strftime on diffusion default name from related model
    - render schedule does not get the correct list
    - diffusions:
        - filter sounds for undiffused diffusions
        - print sounds of diffusions
        - print program's name in lists
    - player:
        - "listen" + "favorite" buttons made easy + automated
        - mixcloud
        - seek bar
    - load complete week for a schedule?
    - list of played diffusions and tracks when non-stop;




