This application defines all base classes for the aircox platform. This includes:
* **Metadata**:         generic class that contains metadata
* **Publication**:      generic class for models that can be publicated
* **Track**:            informations on a track in a playlist
* **SoundFile**:        informations on a sound (podcast)
* **Schedule**:         schedule informations for programs
* **Article**:          simple article
* **Program**:          radio program
* **Episode**:          occurence of a radio program
* **Event**:            log info on what has been or what should be played


# Program
Each program has a directory in **AIRCOX_PROGRAMS_DATA**; For each, subdir:
* **public**:   public sound files and data (accessible from the website)
* **private**:  private sound files and data
* **podcasts**: podcasts that can be upload to external plateforms


# Event
Event have a double purpose:
- log played sounds
- plannify diffusions


# manage.py schedule
Return the next songs to be played and the schedule and the programmed emissions

# manage.py monitor
The manage.py has a command **monitor** that:
* check for new sound files
* stat the sound files
* match sound files against episodes and eventually program them
* upload public podcasts to mixcloud if required

The command will try to match file name against a planified episode by detecting
a date (ISO 8601 date notation YYYY-MM-DD or YYYYMMDD) as name prefix

Tags set:
* **incorrect**:    the sound is not correct for diffusion (TODO: parameters)









