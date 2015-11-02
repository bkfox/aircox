This application defines all base models and basic control of them. We have:
* **Nameable**: generic class used in any class needing to be named. Includes some utility functions;
* **Program**: the program itself;
* **Episode**: occurence of a program;
* **Diffusion**: diffusion of an episode in the timetable, linked to an episode (an episode can have multiple diffusions);
* **Schedule**: describes diffusions frequencies for each program;
* **Track**: track informations in a playlist of an episode;
* **Sound**: information about a sound that can be used for podcast or rerun;

# Program
Each program has a directory in **AIRCOX_PROGRAMS_DATA**; For each, subdir:
* **archives**: complete episode record, can be used for diffusions or as a podcast
* **excerpts**: excerpt of an episode, or other elements, can be used as a podcast

Each program has a schedule, defined through multiple schedule elements. This schedule can calculate the next dates of diffusion, if is a rerun (of wich diffusion), etc.

Basically, for each program created, we can define some options, a directory in **AIRCOX_PROGRAMS_DATA**, where subfolders defines some informations about a file.


# Notes
We don't give any view on what should be now, because it is up to the stream generator to give info about what is running.

