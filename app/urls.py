from django.urls import path
from .views import *
from .views_api import *

urlpatterns = [
    path('', home, name='home'),
    path('accounts/signup', signup),
    path('complete_registration', completeRegistration),

    path('users', userHome, name='user-home'),

    path('staff', staffViewTable, name='staff-home'),
    path('staff/map_view', staffViewMap, name='staff-map-view'),

    path('admins', adminViewOrganization, name='admin-home'),
    path('admins/organization/add', addOrganization, name="organization-add"),
    path('admins/organization/update/<int:pk>', updateOrganization, name="organization-update"),    
    path('admins/organization/export', exportOrganization),
    path('admins/organization/import_preview', importOrganizationPreview),
    path('admins/organization/import', importOrganization),

    path('admins/user', adminViewUser, name='admin-user'),
    path('admins/user/add', addUser, name="user-add"),
    path('admins/user/update/<int:pk>', updateUser, name="user-update"),    
    path('admins/user/export', exportUser),
    path('admins/user/import_preview', importUserPreview),
    path('admins/user/import', importUser),

    path('admins/permission', adminViewPermission, name='admin-permission'),
    path('admins/permission/add', addPermission, name="permission-add"),
    path('admins/permission/update/<int:pk>', updatePermission, name="permission-update"),    
    
    path('admins/device_group', adminViewDeviceGroup, name='admin-device-group'),
    path('admins/device_group/add', addDeviceGroup, name="device-group-add"),
    path('admins/device_group/update/<int:pk>', updateDeviceGroup, name="device-group-update"),    
    path('admins/device_group/export', exportDeviceGroup),
    path('admins/device_group/import_preview', importDeviceGroupPreview),
    path('admins/device_group/import', importDeviceGroup),

    path('admins/unregistered_device', adminViewUnregisteredDevice, name='admin-unregistered-device'),
    path('admins/unregistered_device/add', addUnregisteredDevice, name="unregistered-device-add"),
    path('admins/unregistered_device/update/<int:pk>', updateUnregisteredDevice, name="unregistered-device-update"),    
    path('admins/unregistered_device/export', exportUnregisteredDevice),
    path('admins/unregistered_device/import_preview', importUnregisteredDevicePreview),
    path('admins/unregistered_device/import', importUnregisteredDevice),

    path('admins/registered_device', adminViewRegisteredDevice, name='admin-registered-device'),
    path('admins/registered_device/add', addRegisteredDevice, name="registered-device-add"),
    path('admins/registered_device/update/<int:pk>', updateRegisteredDevice, name="registered-device-update"),    
    path('admins/registered_device/export', exportRegisteredDevice),
    path('admins/registered_device/import_preview', importRegisteredDevicePreview),
    path('admins/registered_device/import', importRegisteredDevice),

    path('admins/location_group', adminViewLocationGroup, name='admin-location-group'),
    path('admins/location_group/add', addLocationGroup, name="location-group-add"),
    path('admins/location_group/update/<int:pk>', updateLocationGroup, name="location-group-update"),    
    path('admins/location_group/export', exportLocationGroup),
    path('admins/location_group/import_preview', importLocationGroupPreview),
    path('admins/location_group/import', importLocationGroup),

    path('admins/location', adminViewLocation, name='admin-location'),
    path('admins/location/add', addLocation, name="location-add"),
    path('admins/location/update/<int:pk>', updateLocation, name="location-update"),    
    path('admins/location/export', exportLocation),
    path('admins/location/import_preview', importLocationPreview),
    path('admins/location/import', importLocation),

    path('api/organization/search', searchOrganization),
    path('api/organization/delete/<int:pk>', deleteOrganization),

    path('api/user/search', searchUser),
    path('api/user/delete/<int:pk>', deleteUser),

    path('api/permission/search', searchPermission),
    path('api/permission/delete/<int:pk>', deletePermission),

    path('api/device_group/search', searchDeviceGroup),
    path('api/device_group/delete/<int:pk>', deleteDeviceGroup),

    path('api/unregistered_device/search', searchUnregisteredDevice),    
    path('api/registered_device/search', searchRegisteredDevice),
    path('api/device/delete/<int:pk>', deleteDevice),    
        
    path('api/location_group/search', searchLocationGroup),
    path('api/location_group/delete/<int:pk>', deleteLocationGroup),

    path('api/location/search', searchLocation),
    path('api/location/delete/<int:pk>', deleteLocation),

    path('admins/settings/mail_template', editMailTemplate),
]