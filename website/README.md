# Website
Application that propose a set of different tools that might be common to
different radio projects. This application has been started to avoid to
pollute *aircox.cms* with aircox specific code and models that might not
be used in other cases.

We define here different models and sections that can be used to construct
a website in a fast and simple manner.

# Dependencies
* `django-suit`: admin interface;
* `django-autocomplete-light`: autocompletion in the admin interface;
* `aircox.cms`, `aircox.programs`

# Features
## Models
* **Program**: publication related to a program;
* **Diffusion**: publication related to an initial Diffusion;


## Sections
* **Player**: player widget
* **Diffusions**: generic section list to retrieve diffusions by date, related
  or not to a specific Program. If wanted, can show schedule in the header of
  the section (with indication of reruns).
* **Playlist**: playlist of a given Diffusion

## Admin
Register all models declared upper, uses django-suit features in order to manage
some fields and autocompletion.

