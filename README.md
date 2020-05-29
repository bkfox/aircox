![](/logo.png)

Platform to manage a radio, schedules, website, and so on. We use the power of great tools like Django or Liquidsoap.

This project is distributed under GPL version 3. More information in the LICENSE file, except for some files whose license is indicated.


## Features
* **streams**: multiple random music streams when no program is played. We also can specify a time range and frequency for each;
* **diffusions**: generate diffusions time slot for programs that have schedule informations. Check for conflicts and rerun.
* **liquidsoap**: create a configuration to use liquidsoap as a stream generator. Also provides interface and control to it;
* **sounds**: each programs have a folder where sounds can be put, that will be detected by the system. Quality can be check and reported for later use. Later, we plan to have uploaders to external plateforms. Sounds can be defined as excerpts or as archives.
* **cms**: application that can be used as basis for website;
* **log**: keep a trace of every played/loaded sounds on the stream generator.


## Scripts
Are included various configuration scripts that can be used to ease setup. They
assume that the project is present in `/srv/apps/aircox`:

* cron: daily cron configuration for the generation of the diffusions
* supervisorctl: audio stream generation, website, sounds monitoring
* nginx: sample config file (must be adapted)

The scripts are written with a combination of `cron`, `supervisord`, `nginx`
and `gunicorn` in mind.


## Installation
Later we plan to have an installation script to reduce the number of above steps.

### Dependencies
For python dependencies take a peek at the `requirements.txt` file, plus
dependencies specific to Django (e.g. for database: `mysqlclient` for MySql
database server).

External applications & modules:
* `liquidsoap`: `aircox` (generation of the audio streams)
* `sox`: `aircox` (check sounds quality and metadatas)
* `gunicorn`: WSGI server to be used in production (installed along as dependency)
* `supervisord`: supervisor
* note there might be external dependencies for python's Pillow too
* sqlite, mysql or any database library that you need to run a database, that is supported by Django (+ eventual python deps)
* gzip: archive logs

Development dependencies:
* `npm`, `webpack`: thoses are used for assets managements and development.

### Setup environment
All scripts and files assumes that:
- you have cloned aircox in `/srv/apps/` (such as `/srv/apps/aircox/README.md`)
- you have a supervisor running (we have scripts for `supervisord`)
- you want to use `gunicorn` as WSGI server (otherwise, you'll need to remove it from the requirement list)

This installation process uses a virtualenv, including all provided scripts.

```
# setup virtual env and activate
virtualenv venv
source venv/bin/activate
# install requirements
pip install -r requirements.txt
```

### Configuration
You must write a settings.py file in the `instance` directory (you can just
copy and paste `instance/sample_settings.py`.

You will need to define a secret key, and eventually update the list of allowed hosts:

```
# django's project secret key (mandatory; you can find generators online)
SECRET_KEY = ''
# list of allowed hosts
ALLOWED_HOSTS = [ '127.0.0.1:8042' ]
```

You also want to redefine the following variable (required by Wagtail for the CMS):

```
WAGTAIL_SITE_NAME = 'Aircox'
```

Each application have a `settings.py` that defines extra options that can be redefined in this file. Look in their respective directories for more informations.


### Installation and first run
Create the database if needed, and generate the tables:

```bash
# apply dependencies' migrations
./manage.py makemigrations
# create the database
./manage.py migrate --fake-initial
# create a super-user (needed in order to access the administration)
./manage.py createsuperuser
```

You must then configure the programs, schedules and audio streams. Start the
server from this directory:

```bash
./manage.py runserver
```

You can access to the django admin interface at `http://127.0.0.1:8000/admin`
and to the cms interface at `http://127.0.0.1:8000/cms/`.

From the admin interface:
* create a Station
* create all the Programs and complete their Schedules
* defines Outputs for the streamer (look at Liquidsoap documentation for
  more information on how to configure it)

TODO: cms related documentation here

Once the configuration is okay, you must start the *controllers monitor*,
that creates configuration file for the audio streams using the new information
and that runs the appropriate application (note that you dont need to restart it
after adding a program that is based on schedules).

If you use supervisord and our script with it, you can use the services defined
in it instead of running commands manually.

## More informations
There are extra informations in `aircox/README.md`.

