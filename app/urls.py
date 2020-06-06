from django.urls import path
from . import views, views_admin, views_staff, views_user, views_api

urlpatterns = [    
    path('', views.home, name='home'),
    path('privacy', views.privacy),
    path('accounts/signup', views.signup),
    path('complete_registration', views.completeRegistration),
    path('profile/update', views.updateAccount),
    path('profile/change_password', views.changePassword),

    path('users', views_user.home, name='user-home'),
    
    # Admin pages
    path('_admin', views_admin.listOrganization, name='admin-home'),
    path('_admin/organizations/add', views_admin.addOrganization),
    path('_admin/organizations/update/<int:pk>', views_admin.updateOrganization),    
    path('_admin/organizations/export', views_admin.exportOrganization),
    path('_admin/organizations/import_preview', views_admin.importOrganizationPreview),
    path('_admin/organizations/import', views_admin.importOrganization),
    path('_admin/organizations/resend_mail/<int:pk>', views_admin.resendMail),

    path('_admin/devices/unregistered', views_admin.listUnregisteredDevice, name='admin-unregistered-device'),
    path('_admin/devices/unregistered/add', views_admin.addUnregisteredDevice),
    path('_admin/devices/unregistered/update/<int:pk>', views_admin.updateUnregisteredDevice),    
    path('_admin/devices/unregistered/export', views_admin.exportUnregisteredDevice),
    path('_admin/devices/unregistered/import_preview', views_admin.importUnregisteredDevicePreview),
    path('_admin/devices/unregistered/import', views_admin.importUnregisteredDevice),

    path('_admin/devices/registered', views_admin.listRegisteredDevice, name='admin-registered-device'),

    path('_admin/settings/admin_mail_template', views_admin.editAdminMailTemplate),
    path('_admin/settings/mail_template', views_admin.editMailTemplate),
    path('_admin/settings/system_params', views_admin.editSystemParams),

    # Tenant pages
    path('staff', views_staff.tableView),
    path('staff/map_view', views_staff.mapView),

    path('staff/users', views_staff.listUser, name='staff-user'),
    path('staff/users/add', views_staff.addUser),
    path('staff/users/update/<int:pk>', views_staff.updateUser),    
    path('staff/users/export', views_staff.exportUser),
    path('staff/users/import_preview', views_staff.importUserPreview),
    path('staff/users/import', views_staff.importUser),
    path('staff/users/resend_mail/<int:pk>', views_staff.resendMail),
    path('staff/users/lock/<int:pk>', views_staff.lockUser),
    path('staff/users/unlock/<int:pk>', views_staff.unlockUser),

    path('staff/locations', views_staff.listLocation, name='staff-location'),
    path('staff/locations/add', views_staff.addLocation),
    path('staff/locations/update/<int:pk>', views_staff.updateLocation),  
    path('staff/locations/export', views_staff.exportLocation),
    path('staff/locations/import_preview', views_staff.importLocationPreview),
    path('staff/locations/import', views_staff.importLocation), 

    path('staff/devices', views_staff.listDevice, name='staff-device'),
    path('staff/devices/add', views_staff.addDevice),
    path('staff/devices/update/<int:pk>', views_staff.updateDevice,),    
        
    path('staff/reports/check_in', views_staff.reportCheckIn),
    path('staff/reports/check_in/export_pdf', views_staff.reportCheckInExportPdf),
    
    path('staff/reports/log_in', views_staff.reportLogIn),
    path('staff/reports/log_in/export_pdf', views_staff.reportLogInExportPdf),

    path('staff/settings/organization', views_staff.configureOranization),

    # API
    path('api/test', views_api.test),
    path('api/login', views_api.logIn),
    path('api/login/search', views_api.searchLogIn),
    path('api/get_user_config', views_api.getUserConfig),

    path('api/checkin', views_api.checkIn),
    path('api/checkin/search', views_api.searchCheckIn),
    path('api/checkin/last_updated', views_api.getLastCheckInTime),
    path('api/checkin/check_for_update', views_api.checkForNewCheckIn),
    
    path('api/organization/search',  views_api.searchOrganization),
    path('api/organization/details/<int:pk>', views_api.viewOrganizationDetails),
    path('api/organization/delete/<int:pk>', views_api.deleteOrganization),

    path('api/user/search', views_api.searchUser),
    path('api/user/details/<int:pk>', views_api.viewUserDetails),
    path('api/user/delete/<int:pk>', views_api.deleteUser),

    path('api/device/unregistered/search', views_api.searchUnregisteredDevice),    
    path('api/device/registered/search', views_api.searchRegisteredDevice),
    path('api/device/search_by_org', views_api.searchDeviceByOrganization),
    path('api/device/delete/<int:pk>', views_api.deleteDevice),    
    path('api/device/delete_from_org/<int:pk>', views_api.deleteDeviceFromOrg),    

    path('api/location/search', views_api.searchLocation),
    path('api/location/delete/<int:pk>', views_api.deleteLocation),
    
]