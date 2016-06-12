from django.contrib import admin
import aircox.liquidsoap.models as models

@admin.register(models.Output)
class OutputAdmin (admin.ModelAdmin):
    list_display = ('id', 'type')


