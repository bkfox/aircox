# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers
import django.db.models.deletion
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now, verbose_name='date')),
                ('published', models.BooleanField(default=True, verbose_name='public')),
                ('title', models.CharField(verbose_name='titre', max_length=128)),
                ('content', models.TextField(null=True, blank=True, verbose_name='description')),
                ('image', models.ImageField(null=True, blank=True, upload_to='')),
                ('static_page', models.BooleanField(default=False, verbose_name='page statique')),
                ('focus', models.BooleanField(default=False, verbose_name="l'article est épinglé")),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, verbose_name='auteur')),
                ('tags', taggit.managers.TaggableManager(through='taggit.TaggedItem', to='taggit.Tag', blank=True, help_text='A comma-separated list of tags.', verbose_name='mots-clés')),
            ],
            options={
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
            },
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('post_id', models.PositiveIntegerField()),
                ('post_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, help_text='the publication is posted on this thread', blank=True, to='aircox_cms.Thread'),
        ),
    ]
