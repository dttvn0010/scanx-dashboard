from django.urls import path
from .views import *
from .views_api import *

urlpatterns = [
    path('', home, name='home'),
    path('accounts/signup', signup),
    path('complete_registration', completeRegistration),

    path('users', userViewTable, name='user-home'),
    path('users/map_view', userViewMap, name='user-map-view'),

    path('admins', adminViewOrganization, name='admin-home'),
    path('admins/organization/add', addOrganization, name="organization-add"),
    path('admins/organization/update/<int:pk>', updateOrganization, name="organization-update"),
    path('admins/organization/delete/<int:pk>', deleteOrganization, name="organization-delete"),
    path('admins/organization/export', exportOrganization),
    path('admins/organization/import', importOrganization),
    
    path('admins/unregistered_device', adminViewUnregisteredDevice, name='admin-unregistered-device'),
    path('admins/unregistered_device/add', addUnregisteredDevice, name="unregistered-device-add"),
    path('admins/unregistered_device/update/<int:pk>', updateUnregisteredDevice, name="unregistered-device-update"),
    path('admins/unregistered_device/delete/<int:pk>', deleteUnregisteredDevice, name="unregistered-device-delete"),
    path('admins/unregistered_device/export', exportUnregisteredDevice),
    path('admins/unregistered_device/import', importUnregisteredDevice),

    path('admins/registered_device', adminViewRegisteredDevice, name='admin-registered-device'),
    path('admins/registered_device/add', addRegisteredDevice, name="registered-device-add"),
    path('admins/registered_device/update/<int:pk>', updateRegisteredDevice, name="registered-device-update"),
    path('admins/registered_device/delete/<int:pk>', deleteRegisteredDevice, name="registered-device-delete"),
    path('admins/registered_device/export', exportRegisteredDevice),
    path('admins/registered_device/import', importRegisteredDevice),

    path('api/organization/search', searchOrganization),
    path('api/unregistered_device/search', searchUnregisteredDevice),
    path('api/registered_device/search', searchRegisteredDevice),

    path('admins/settings/mail_template', editMailTemplate),
]