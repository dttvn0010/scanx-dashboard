# Generated by Django 3.0.6 on 2020-05-12 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20200512_0023'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='createdDate',
            field=models.DateTimeField(null=True),
        ),
    ]
