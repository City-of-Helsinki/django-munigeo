# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0002_auto_20150608_1607'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='modified_at',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 2, 0), help_text='Time when the information was last changed', auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='street',
            name='modified_at',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 2, 0), help_text='Time when the information was last changed', auto_now=True),
            preserve_default=False,
        ),
    ]
