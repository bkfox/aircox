- sounds monitor: max_size of path, take in account
- logs: archive functionnality + track stats for diffusions
- debug/prod configuration

# TODO:
- general:
    - timezone shit
    - translation

- programs:
    - schedule: potential issue with nth' week of month
    - tests:
        - sound_monitor

- liquidsoap:
    - models to template
    - tests:
        - monitor
        - check when a played sound has a temp blank

- cms:
    - empty content -> empty string
    - update documentation:
        - cms.views
        - cms.exposure
        - cms.script
        - cms.qcombine
    - routes
        - tag name instead of tag slug for the title
        - optional url args
    - admin cms
    - content management -> do we use a markup language?
    - sections:
        - calendar
        - article list with the focus
            -> set html attribute based on values that are public

- website:
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
    - search input in a section






