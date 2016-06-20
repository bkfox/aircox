- sounds monitor: max_size of path, take in account
- logs: archive functionnality + track stats for diffusions
- debug/prod configuration

# TODO:
- general:
    - timezone shit

- programs:
    - schedule:
        - (old) schedule.to_string unused? commented
        - write more tests
    - sounds:
        - check that a sound is available when uploading too
        - one sound, one diffusion
          -> sound_monitor
          -> liquidsoap
          -> tests: sound_monitor, liquidsoap (monitor)

- liquidsoap:
    - update rc's supervisor scripts
    - check when a played sound has a temp blank

- cms:
    - empty content -> empty string
    - update documentation:
        - cms.views
        - cms.parts
        - cms.script
        - cms.qcombine
    - routes
        - integrate QCombine
    - admin cms
    - content management -> do we use a markup language?
    - sections:
        - similar articles (using tags)
        - calendar
        - article list with the focus
            -> set html attribute based on values that are public
    - tags: allow tags_url route QCombine

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
    - finish that fucking website
    - list of played diffusions and tracks when non-stop;
    - search field -- section






