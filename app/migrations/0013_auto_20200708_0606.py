# Generated by Django 3.0.6 on 2020-07-08 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20200708_0356'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
    ]