![](/data/logo.png)

Platform to manage a radio, schedules, website, and so on. We use the power of Django and Liquidsoap.

## Current features
* **streams**: multiple random music streams when no program is played. We also can specify a time range and frequency;
* **diffusions**: generate diffusions time slot for programs that have schedule informations. Check for conflicts and rerun.
* **liquidsoap**: create a configuration to use liquidsoap as a stream generator. Also provides interface and control to it;
* **sounds**: each programs have a folder where sounds can be put, that will be detected by the system. Quality can be check and reported for later use. Later, we plan to have uploaders to external plateforms. Sounds can be defined as excerpts or as archives.
* **cms**: a small CMS to generate a website with all cool informations related to programs and diffusions. On the contrary of some other plateforms, we keep program and content management distinct.
* **log**: keep a trace of every played/loaded sounds on the stream generator.

## Applications
* **programs**: managing stations, programs, schedules and diffusions. This is the core application, that handle most of the work;
* **controllers**: interface with external stream generators. For the moment only support [Liquidsoap](http://liquidsoap.fm/). Generate configuration files, trigger scheduled diffusions and so on;
* **cms**: cms manager with reusable tools (can be used in another website application);
* **website**: set of common models, sections, and other items ready to be used for a website;

## Installation
For now, we provide only applications availables under the aircox directory. Create a django project, and add the aircox applications directory.

Later we would provide a package, but now we have other priorities.

### settings.py
* INSTALLED_APPS:
    - dependencies: `'taggit'` (*programs* and *cms* applications),
                    `'easy_thumbnails'` (*cms*), `'honeypot'` (*cms*)
    - optional dependencies (in order to make users' life easier): `'autocomplete_light'`, `'suit'`
    - aircox: `'aircox.programs'`, `'aircox.controllers'`, `'aircox.cms'`, `'aircox.website'`

