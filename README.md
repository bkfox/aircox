![](/data/logo.png)

Platform to manage a radio, schedules, website, and so on. We use the power of great tools like Django or Liquidsoap.

## Current features
* **streams**: multiple random music streams when no program is played. We also can specify a time range and frequency;
* **diffusions**: generate diffusions time slot for programs that have schedule informations. Check for conflicts and rerun.
* **liquidsoap**: create a configuration to use liquidsoap as a stream generator. Also provides interface and control to it;
* **sounds**: each programs have a folder where sounds can be put, that will be detected by the system. Quality can be check and reported for later use. Later, we plan to have uploaders to external plateforms. Sounds can be defined as excerpts or as archives.
* **cms**: application that can be used as basis for website (we use Wagtail; if you don't want it this application is not required to make everything run);
* **log**: keep a trace of every played/loaded sounds on the stream generator.

## Applications
* **programs**: managing stations, programs, schedules and diffusions. This is the core application, that handle most of the work;
* **controllers**: interface with external stream generators. For the moment only support [Liquidsoap](http://liquidsoap.fm/). Generate configuration files, trigger scheduled diffusions and so on;
* **cms**: defines models and templates to generate a website connected to Aircox;

## Installation
For now, we provide only applications availables under the aircox directory. Create a django project, and add the aircox applications directory.

Later we would provide a package, but now we have other priorities.

Dependencies:
* wagtail (cms)
* honeypot (cms)
* taggit (cms, programs)


