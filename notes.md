This file is used as a reminder, can be used as crappy documentation too.


# conventions
## coding style
* name of classes relative to a class:
    - metaclass: `class_name + 'Meta'`
    - base classes: `class_name + 'Base'`

* import and naming:
    - the imported "models" file in the same application is named "models"
    - the imported "models" file from another application is named with the application's name
    - to avoid conflict:
        - django's settings can be named "main_settings"

## aircox.cms
* icons: cropped to 32x32
* cover in list items: cropped 64x64



# To discuss / To think
- aircox_cms.signals: handle renaming of the program if the article's title has
    not been changed -> need to cache of the title at __init__
- ensure per station website for all generated publications
- aircox_cms: remove "station" fields when it is possible in the pages & sections


# Long term TODO
programs:
    - sounds monitor: max_size of path, take in account
    - archives can be set afterwards for rerun, so check must be done
        at the same time we monitor
    - logs: archive functionnality
    - tools:
        - track stats for diffusions

cms:
    - player support diffusions with multiple archive files
    - comments -> remove/edit by the author


# error when generating diffusions (when all page of a page have been removed):
seems like the numchild attribute is not updated correctly when calling page.delete()

    ```
    File "/srv/apps/aircox/venv/lib/python3.5/site-packages/treebeard/mp_tree.py", line 977, in add_child
        return MP_AddChildHandler(self, **kwargs).process()
    File "/srv/apps/aircox/venv/lib/python3.5/site-packages/treebeard/mp_tree.py", line 360, in process
        newobj.path = self.node.get_last_child()._inc_path()
    AttributeError: 'NoneType' object has no attribute '_inc_path'
    ```

# Instance's TODO
- menu_top .sections:
    - display inline block
    - search on the right
- lists > items style
- logo: url
- comments / more info (perhaps using the thing like the player)
- footer url to aircox's repo + admin
- styling cal (a.today colored)

- init of post related models
    -> date is not formatted
    -> missing image?



