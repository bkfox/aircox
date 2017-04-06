# Aircox Programs

This application defines all base models and basic control of them. We have:
* **Nameable**: generic class used in any class needing to be named. Includes some utility functions;
* **Station**: a station
* **Program**: the program itself;
* **Diffusion**: occurrence of a program planified in the timetable. For rerun, informations are bound to the initial diffusion;
* **Schedule**: describes diffusions frequencies for each program;
* **Track**: track informations in a playlist of a diffusion;
* **Sound**: information about a sound that can be used for podcast or rerun;
* **Log**: logs


## Architecture
A Station is basically an object that represent a radio station. On each station, we use the Program object, that is declined in two different types:
* **Scheduled**: the diffusion is based on a timetable and planified through one Schedule or more; Diffusion object represent the occurrence of these programs;
* **Streamed**: the diffusion is based on random playlist, used to fill gaps between the programs;

Each program has a directory in **AIRCOX_PROGRAMS_DIR**; For each, subdir:
* **archives**: complete episode record, can be used for diffusions or as a podcast
* **excerpts**: excerpt of an episode, or other elements, can be used as a podcast


## manage.py's commands
* **diffusions**: update/create, check and clean diffusions based on programs schedules;
* **import_playlist**: import a playlist from a csv file, and associate it to a sound;
* **sound_monitor**: check for existing and missing sounds files in programs directories and synchronize the database. It can check for the quality of file and update sound info.
* **sound_quality_check**: check for the quality of the file (don't update database);
* **streamer**: audio stream generation and control it;


## Requirements
* Sox (and soxi): sound file monitor and quality check
* requirements.txt for python's dependecies

