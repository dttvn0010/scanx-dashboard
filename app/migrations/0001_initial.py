# Generated by Django 3.0.6 on 2020-07-13 02:55

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('fullname', models.CharField(blank=True, max_length=50, null=True, verbose_name='Full Name (*)')),
                ('nfcEnabled', models.BooleanField(blank=True, null=True, verbose_name='nfc.enabled')),
                ('qrScanEnabled', models.BooleanField(blank=True, null=True, verbose_name='qr.scanning.enabled')),
                ('sharedLocation', models.BooleanField(blank=True, null=True, verbose_name='geolocation.enabled')),
                ('profilePicture', models.ImageField(blank=True, null=True, upload_to='static/images')),
                ('status', models.IntegerField(blank=True, null=True)),
                ('tmpPassword', models.CharField(blank=True, max_length=30, null=True)),
                ('tmpPasswordExpired', models.DateTimeField(null=True)),
                ('createdDate', models.DateTimeField(null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='LogAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LogConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelName', models.CharField(max_length=100, unique=True)),
                ('logFields', models.CharField(blank=True, max_length=1000, null=True)),
                ('displayFields', models.CharField(blank=True, max_length=1000, null=True)),
                ('createNotifyTemplate', models.CharField(blank=True, default='', max_length=200)),
                ('acquireNotifyTemplate', models.CharField(blank=True, default='', max_length=200)),
                ('updateNotifyTemplate', models.CharField(blank=True, default='', max_length=200)),
                ('releaseNotifyTemplate', models.CharField(blank=True, default='', max_length=200)),
                ('deleteNotifyTemplate', models.CharField(blank=True, default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='MailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('subject', models.CharField(max_length=200)),
                ('body', models.TextField(blank=True)),
                ('customizedByTenants', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Company Name * ')),
                ('adminUsername', models.CharField(max_length=150, null=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('nfcEnabled', models.BooleanField(default=False, verbose_name='nfc.enabled')),
                ('qrScanEnabled', models.BooleanField(default=False, verbose_name='qr.scanning.enabled')),
                ('geoLocationEnabled', models.BooleanField(default=False, verbose_name='geolocation.enabled')),
                ('active', models.BooleanField(default=False, verbose_name='active')),
                ('createdDate', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SystemParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=50)),
                ('value', models.CharField(blank=True, max_length=500, null=True)),
                ('min', models.CharField(blank=True, max_length=50, null=True)),
                ('max', models.CharField(blank=True, max_length=50, null=True)),
                ('maxLength', models.IntegerField(blank=True, null=True)),
                ('customizedByTenants', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='TenantParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(blank=True, max_length=500, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Organization')),
                ('parameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.SystemParameter')),
            ],
        ),
        migrations.CreateModel(
            name='LogIn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fromMobileApp', models.BooleanField()),
                ('date', models.DateTimeField()),
                ('organization', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelName', models.CharField(default='', max_length=100)),
                ('objectId', models.IntegerField(null=True)),
                ('actionDate', models.DateTimeField()),
                ('preContent', models.TextField(null=True)),
                ('postContent', models.TextField(null=True)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app.LogAction')),
                ('organization', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Organization')),
                ('performUser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('viewUsers', models.ManyToManyField(related_name='view_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('addressLine1', models.CharField(max_length=100, verbose_name='Address Line 1 (*)')),
                ('addressLine2', models.CharField(blank=True, max_length=100, null=True, verbose_name='addressLine2')),
                ('city', models.CharField(max_length=50, verbose_name='City (*)')),
                ('postCode', models.CharField(max_length=10, verbose_name='Post Code (*)')),
                ('createdDate', models.DateTimeField(null=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id1', models.CharField(max_length=30, verbose_name='ID#1 (*)')),
                ('id2', models.CharField(max_length=30, verbose_name='ID#2 (*)')),
                ('uid', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='uid')),
                ('lat', models.FloatField(null=True)),
                ('lng', models.FloatField(null=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True, verbose_name='description')),
                ('registeredDate', models.DateTimeField(blank=True, null=True)),
                ('status', models.IntegerField(blank=True, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('createdDate', models.DateTimeField(null=True)),
                ('installationLocation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Location')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='CheckIn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scanCode', models.CharField(blank=True, max_length=50, null=True)),
                ('uid', models.CharField(blank=True, max_length=50, null=True)),
                ('lat', models.FloatField(null=True)),
                ('lng', models.FloatField(null=True)),
                ('date', models.DateTimeField()),
                ('status', models.IntegerField(null=True)),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Device')),
                ('location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Location')),
                ('organization', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Organization'),
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(to='app.Role', verbose_name='Role (*)'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
