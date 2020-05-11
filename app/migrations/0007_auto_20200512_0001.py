# Generated by Django 3.0.6 on 2020-05-11 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20200512_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='app.Organization'),
        ),
    ]
