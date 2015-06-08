# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='municipality',
            name='division',
            field=models.OneToOneField(related_name='muni', to='munigeo.AdministrativeDivision', null=True),
        ),
    ]
