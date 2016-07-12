from django.contrib import admin

import aircox.controllers.models as models

#@admin.register(Log)
#class LogAdmin(admin.ModelAdmin):
#    list_display = ['id', 'date', 'source', 'comment', 'related_object']
#    list_filter = ['date', 'source', 'related_type']

admin.site.register(models.Station)
admin.site.register(models.Source)
admin.site.register(models.Output)
admin.site.register(models.Log)




