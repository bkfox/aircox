# Aircox
Aircox application aims to provide basis of a radio management system.

## Architecture
A Station contains programs that can be scheduled or streamed. A *Scheduled Program* is a regular show that has planified diffusions of its occurences (episodes). A *Streamed Program* is a program used to play randoms musics between the shows.

Each program has a directory on the server where user puts its podcasts (in **AIRCOX_PROGRAM_DIR**). It contains the directories **archives** (complete show's podcasts) and **excerpts** (partial or whatever podcasts).


## manage.py's commands
* **diffusions**: update/create, check and clean diffusions based on programs schedules;
* **import_playlist**: import a playlist from a csv file, and associate it to a sound;
* **sound_monitor**: check for existing and missing sounds files in programs directories and synchronize the database. It can check for the quality of file and update sound info.
* **sound_quality_check**: check for the quality of the file (don't update database);
* **streamer**: audio stream generation and control it;


## Requirements
* Sox (and soxi): sound file monitor and quality check
* requirements.txt for python's dependecies

