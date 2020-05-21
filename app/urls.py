from django.urls import path
from . import views, views_admin, views_staff, views_user, views_api

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup', views.signup),
    path('complete_registration', views.completeRegistration),

    path('users', views_user.home, name='user-home'),

    # Admin pages
    path('_admin', views_admin.listOrganization, name='admin-home'),
    path('_admin/organization/add', views_admin.addOrganization),
    path('_admin/organization/update/<int:pk>', views_admin.updateOrganization),    
    path('_admin/organization/export', views_admin.exportOrganization),
    path('_admin/organization/import_preview', views_admin.importOrganizationPreview),
    path('_admin/organization/import', views_admin.importOrganization),

    path('_admin/permission', views_admin.listPermission, name='admin-permission'),
    path('_admin/permission/add', views_admin.addPermission),
    path('_admin/permission/update/<int:pk>', views_admin.updatePermission),    
    
    path('_admin/device/unregistered', views_admin.listUnregisteredDevice, name='admin-unregistered-device'),
    path('_admin/device/unregistered/add', views_admin.addUnregisteredDevice),
    path('_admin/device/unregistered/update/<int:pk>', views_admin.updateUnregisteredDevice),    
    path('_admin/device/unregistered/export', views_admin.exportUnregisteredDevice),
    path('_admin/device/unregistered/import_preview', views_admin.importUnregisteredDevicePreview),
    path('_admin/device/unregistered/import', views_admin.importUnregisteredDevice),

    path('_admin/device/registered', views_admin.listRegisteredDevice, name='admin-registered-device'),

    path('_admin/settings/mail_template', views_admin.editMailTemplate),

    # Tenant pages
    path('staff', views_staff.tableView),
    path('staff/map_view', views_staff.mapView),

    path('staff/user', views_staff.listUser, name='staff-user'),
    path('staff/user/add', views_staff.addUser),
    path('staff/user/update/<int:pk>', views_staff.updateUser),    
    path('staff/user/export', views_staff.exportUser),
    path('staff/user/import_preview', views_staff.importUserPreview),
    path('staff/user/import', views_staff.importUser),


    path('staff/device', views_staff.listDevice, name='staff-device'),
    path('staff/device/add', views_staff.addDevice),
    path('staff/device/update/<int:pk>', views_staff.updateDevice,),    
    path('staff/device/delete/<int:pk>', views_staff.deleteDevice),    

    path('staff/location', views_staff.listLocation, name='staff-location'),
    path('staff/location/add', views_staff.addLocation),
    path('staff/location/update/<int:pk>', views_staff.updateLocation),  
    path('staff/location/export', views_staff.exportLocation),
    path('staff/location/import_preview', views_staff.importLocationPreview),
    path('staff/location/import', views_staff.importLocation),  

    # API
    path('api/test', views_api.test),
    path('api/checkin', views_api.checkIn),
    path('api/checkin/search', views_api.searchCheckIn),
    
    path('api/organization/search',  views_api.searchOrganization),
    path('api/organization/delete/<int:pk>', views_api.deleteOrganization),

    path('api/user/search', views_api.searchUser),
    path('api/user/delete/<int:pk>', views_api.deleteUser),

    path('api/permission/search', views_api.searchPermission),
    path('api/permission/delete/<int:pk>', views_api.deletePermission),

    path('api/device/unregistered/search', views_api.searchUnregisteredDevice),    
    path('api/device/registered/search', views_api.searchRegisteredDevice),
    path('api/device/search_by_org', views_api.searchDeviceByOrganization),
    path('api/device/delete/<int:pk>', views_api.deleteDevice),    

    path('api/location/search', views_api.searchLocation),
    path('api/location/delete/<int:pk>', views_api.deleteLocation),
    
]