# Generated by Django 3.1.5 on 2021-02-27 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20210227_1010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, null=True, to='app.Group', verbose_name='group'),
        ),
    ]