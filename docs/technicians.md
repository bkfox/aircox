
# General information
Aircox is a set of Django applications that aims to provide a radio management solution, and is
written in Python 3.5.

Running Aircox on production involves:
* Aircox modules and a running Django project;
* a supervisor for common tasks (sounds monitoring, stream control, etc.) -- `supervisord`;
* a wsgi and an HTTP server -- `gunicorn`, `nginx`;
* a database supported by Django (MySQL, SQLite, PostGresSQL);

# Architecture and concepts
Aircox is divided in three main modules:
* `programs`: basics of Aircox (programs, diffusions, sounds, etc. management);
* `controllers`: interact with application to generate audio stream (LiquidSoap);
* `cms`: create a website with Aircox elements (playlists, timetable, players on the website);





# Installation


# Configuration



