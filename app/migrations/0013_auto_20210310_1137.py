# Generated by Django 3.1.5 on 2021-03-10 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20210310_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='isReseller',
            field=models.BooleanField(default=False, null=True, verbose_name='is.reseller'),
        ),
    ]