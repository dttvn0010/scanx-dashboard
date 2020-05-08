from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import forms, models

class MyUserAdmin(UserAdmin):
    add_form = forms.MyUserCreationForm
    form = forms.MyUserChangeForm
    model = models.User
    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (                      # new fieldset added on to the bottom
            'Other information',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'fullname', 'organization'
                ),
            },
        ),
    )
    list_display = ['username', 'fullname', 'email', 'organization']

admin.site.register(models.Organization)
admin.site.register(models.LocationGroup)
admin.site.register(models.Location)
admin.site.register(models.DeviceType)
admin.site.register(models.DeviceGroup)
admin.site.register(models.Device)
admin.site.register(models.User, MyUserAdmin)
