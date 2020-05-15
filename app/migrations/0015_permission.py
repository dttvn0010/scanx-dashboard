# Generated by Django 3.0.6 on 2020-05-15 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20200515_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('accessFunctions', models.CharField(blank=True, max_length=10000)),
                ('viewFunctions', models.CharField(blank=True, max_length=10000)),
                ('editFunctions', models.CharField(blank=True, max_length=10000)),
                ('deleteFunctions', models.CharField(blank=True, max_length=10000)),
                ('createdDate', models.DateTimeField(null=True)),
            ],
        ),
    ]
