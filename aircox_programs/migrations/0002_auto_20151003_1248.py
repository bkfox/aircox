# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aircox_programs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diffusion',
            name='type',
            field=models.SmallIntegerField(choices=[(4, 'stop'), (2, 'cancel'), (1, 'unconfirmed'), (0, 'default')], verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='frequency',
            field=models.SmallIntegerField(choices=[(31, 'every'), (8, 'fourth'), (5, 'first and third'), (10, 'second and fourth'), (16, 'last'), (32, 'one on two'), (4, 'third'), (1, 'first'), (2, 'second')], verbose_name='fréquence'),
        ),
    ]
