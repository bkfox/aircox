# Aircox
Platform to manage a radio. We use the power of Django

## Current features
* **streams**: multiple random music streams when no program is played. We also can specify a time range and frequency;
* **diffusions**: generate diffusions time slot for programs that have schedule informations. Check for conflicts and rerun.
* **liquidsoap**: create a configuration to use liquidsoap as a stream generator. Also provides interface and control to it;
* **sounds**: each programs have a folder where sounds can be put, that will be detected by the system. Quality can be check and reported for later use. Later, we plan to have uploaders to external plateforms. Sounds can be defined as excerpts or as archives.
* **cms**: a small CMS to generate a website with all cool informations related to programs and diffusions. On the contrary of other plateform, we keep programs and content management seperate.
* **log**: keep a trace of every played/loaded sounds on the stream generator.

## Applications
* **programs**: managing stations, programs, schedules and diffusions. This is the core application, that handle most of the work.
* **cms**: cms manager with reusable tools.
* **liquidsoap**: liquidsoap controls.


