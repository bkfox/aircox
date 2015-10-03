# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Diffusion',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('type', models.SmallIntegerField(choices=[(0, 'default'), (4, 'stop'), (1, 'unconfirmed'), (2, 'cancel')], verbose_name='type')),
                ('date', models.DateTimeField(verbose_name='start of the diffusion')),
            ],
            options={
                'verbose_name': 'Diffusion',
                'verbose_name_plural': 'Diffusions',
            },
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='nom', max_length=128)),
            ],
            options={
                'verbose_name': 'Épisode',
                'verbose_name_plural': 'Épisodes',
            },
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='nom', max_length=128)),
                ('active', models.BooleanField(default=True, help_text='if not set this program is no longer active', verbose_name='inactive')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('date', models.DateTimeField(verbose_name='date')),
                ('duration', models.TimeField(verbose_name='durée')),
                ('frequency', models.SmallIntegerField(choices=[(4, 'third'), (32, 'one on two'), (10, 'second and fourth'), (5, 'first and third'), (31, 'every'), (2, 'second'), (1, 'first'), (16, 'last'), (8, 'fourth')], verbose_name='fréquence')),
                ('program', models.ForeignKey(to='aircox_programs.Program', null=True, blank=True)),
                ('rerun', models.ForeignKey(to='aircox_programs.Schedule', null=True, help_text='Schedule of a rerun of this one', blank=True, verbose_name='rediffusion')),
            ],
            options={
                'verbose_name': 'Schedule',
                'verbose_name_plural': 'Schedules',
            },
        ),
        migrations.CreateModel(
            name='Sound',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='nom', max_length=128)),
                ('path', models.FilePathField(recursive=True, match='*(.ogg|.flac|.wav|.mp3|.opus)$', path='/media/data/courants/code/aircox/static/media/programs', null=True, blank=True, verbose_name='fichier')),
                ('embed', models.TextField(null=True, blank=True, help_text='if set, consider the sound podcastable', verbose_name='embed HTML code from external website')),
                ('duration', models.TimeField(null=True, blank=True, verbose_name='durée')),
                ('public', models.BooleanField(default=False, help_text='the element is public', verbose_name='public')),
                ('fragment', models.BooleanField(default=False, help_text='the file is a cut', verbose_name='son incomplet')),
                ('removed', models.BooleanField(default=False, help_text='this sound has been removed from filesystem')),
            ],
            options={
                'verbose_name': 'Sound',
                'verbose_name_plural': 'Sounds',
            },
        ),
        migrations.CreateModel(
            name='Stream',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(null=True, blank=True, verbose_name='nom', max_length=32)),
                ('public', models.BooleanField(default=True, help_text='program list is public', verbose_name='public')),
                ('type', models.SmallIntegerField(choices=[(1, 'schedule'), (0, 'random')], verbose_name='type')),
                ('priority', models.SmallIntegerField(default=0, help_text='priority of the stream', verbose_name='priority')),
            ],
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(verbose_name='nom', max_length=128)),
                ('artist', models.CharField(verbose_name='artiste', max_length=128)),
                ('position', models.SmallIntegerField(default=0, help_text='position in the playlist')),
                ('episode', models.ForeignKey(to='aircox_programs.Episode')),
                ('tags', taggit.managers.TaggableManager(through='taggit.TaggedItem', to='taggit.Tag', blank=True, help_text='A comma-separated list of tags.', verbose_name='mots-clés')),
            ],
            options={
                'verbose_name': 'Track',
                'verbose_name_plural': 'Tracks',
            },
        ),
        migrations.AddField(
            model_name='program',
            name='stream',
            field=models.ForeignKey(to='aircox_programs.Stream', verbose_name='stream'),
        ),
        migrations.AddField(
            model_name='episode',
            name='program',
            field=models.ForeignKey(to='aircox_programs.Program', help_text='parent program', verbose_name='program'),
        ),
        migrations.AddField(
            model_name='episode',
            name='sounds',
            field=models.ManyToManyField(to='aircox_programs.Sound', blank=True, verbose_name='sounds'),
        ),
        migrations.AddField(
            model_name='diffusion',
            name='episode',
            field=models.ForeignKey(to='aircox_programs.Episode', null=True, blank=True, verbose_name='épisode'),
        ),
        migrations.AddField(
            model_name='diffusion',
            name='program',
            field=models.ForeignKey(to='aircox_programs.Program', verbose_name='program'),
        ),
        migrations.AddField(
            model_name='diffusion',
            name='stream',
            field=models.ForeignKey(default=0, help_text='stream id on which the diffusion happens', to='aircox_programs.Stream', verbose_name='stream'),
        ),
    ]
