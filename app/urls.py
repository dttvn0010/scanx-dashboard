from django.urls import path
from . import views, views_admin, views_staff, views_user, views_api

urlpatterns = [    
    path('', views.home, name='home'),
    path('privacy', views.privacy),
    path('support', views.support),
    path('accounts/initial_setup', views.initialSetup),
    path('accounts/signup', views.signup),
    path('accounts/forgot_password', views.forgotPassword),
    path('accounts/reset_password', views.resetPassword),
    path('profile/update', views.updateAccount),
    path('profile/change_password', views.changePassword),

    path('users', views_user.home, name='user-home'),
    
    # Admin pages
    path('_admin', views_admin.listOrganizations, name='admin-home'),    
    path('_admin/organizations/add', views_admin.addOrganization),
    path('_admin/organizations/update/<int:pk>', views_admin.updateOrganization),    
    path('_admin/organizations/user_list/<int:pk>', views_admin.listOrganizationUsers),
    path('_admin/organizations/details/<int:pk>', views_admin.viewOrganizationDetails),
    path('_admin/organizations/export', views_admin.exportOrganization),
    path('_admin/organizations/import_preview', views_admin.importOrganizationPreview),
    path('_admin/organizations/import', views_admin.importOrganization),
    path('_admin/organizations/resend_mail/<int:pk>', views_admin.resendMail),

    path('_admin/devices/unregistered', views_admin.listUnregisteredDevices, name='admin-unregistered-device'),
    path('_admin/devices/unregistered/add', views_admin.addUnregisteredDevice),
    path('_admin/devices/unregistered/update/<int:pk>', views_admin.updateUnregisteredDevice),    
    path('_admin/devices/unregistered/export', views_admin.exportUnregisteredDevice),
    path('_admin/devices/unregistered/import_preview', views_admin.importUnregisteredDevicePreview),
    path('_admin/devices/unregistered/import', views_admin.importUnregisteredDevice),

    path('_admin/devices/registered', views_admin.listRegisteredDevices, name='admin-registered-device'),

    path('_admin/settings/system_params', views_admin.editSystemParams),
    path('_admin/settings/mail_templates', views_admin.editMailTemplates),

    path('_admin/logs', views_admin.listLogs, name='admin-log'),
    path('_admin/logs/details/<int:pk>', views_admin.viewLogDetail),

    # Tenant pages
    path('staff', views_staff.home),

    path('staff/dashboard', views_staff.tableView),
    path('staff/map_view', views_staff.mapView),

    path('staff/users', views_staff.listUsers, name='staff-user'),
    path('staff/users/add', views_staff.addUser),
    path('staff/users/update/<int:pk>', views_staff.updateUser),    
    path('staff/users/export', views_staff.exportUser),
    path('staff/users/import_preview', views_staff.importUserPreview),
    path('staff/users/import', views_staff.importUser),
    path('staff/users/resend_mail/<int:pk>', views_staff.resendMail),

    path('staff/locations', views_staff.listLocations, name='staff-location'),
    path('staff/locations/add', views_staff.addLocation),
    path('staff/locations/update/<int:pk>', views_staff.updateLocation),  
    path('staff/locations/export', views_staff.exportLocation),
    path('staff/locations/import_preview', views_staff.importLocationPreview),
    path('staff/locations/import', views_staff.importLocation), 

    path('staff/devices', views_staff.listDevices, name='staff-device'),
    path('staff/devices/add', views_staff.addDevice),
    path('staff/devices/update/<int:pk>', views_staff.updateDevice),    
        
    path('staff/groups', views_staff.listGroups, name='staff-group'),
    path('staff/groups/add', views_staff.addGroup),
    path('staff/groups/update/<int:pk>', views_staff.updateGroup),  
    path('staff/groups/permissions/<int:pk>', views_staff.setGroupPermission),  

    path('staff/reports/check_in', views_staff.reportCheckIn),
    path('staff/reports/check_in/export_pdf', views_staff.reportCheckInExportPdf),
    
    path('staff/reports/log_in', views_staff.reportLogIn),
    path('staff/reports/log_in/export_pdf', views_staff.reportLogInExportPdf),

    path('staff/logs', views_staff.listLogs, name='staff-log'),
    path('staff/logs/details/<int:pk>', views_staff.viewLogDetail),

    path('staff/settings/organization', views_staff.configureOranization),
    path('staff/settings/custom_params', views_staff.editCustomParams),
    path('staff/app_info', views_staff.appInfo),

    # API
    path('api/login', views_api.logIn),
    path('api/login/search', views_api.searchLogIn),

    path('api/checkin/search', views_api.searchCheckIn),
    path('api/checkin/last_updated', views_api.getLastCheckInTime),
    path('api/checkin/check_for_update', views_api.checkForNewCheckIn),
    
    path('api/organization/search',  views_api.searchOrganization),
    path('api/organization/delete/<int:pk>', views_api.deleteOrganization),

    path('api/user/get_info', views_api.getUserInfo),    
    path('api/user/checkin', views_api.userCheckIn),
    path('api/user/get_checkin_history', views_api.getUserCheckInHistory),
    path('api/user/change_password', views_api.changeUserPassword),
    path('api/user/update_profile', views_api.updateUserProfile),

    path('api/user/search', views_api.searchUser),
    path('api/user/get_by_organization', views_api.getUsersByOrganization),
    path('api/user/details/<int:pk>', views_api.viewUserDetails),
    path('api/user/delete/<int:pk>', views_api.deleteUser),
    path('api/user/disable/<int:pk>', views_api.disableUser),    
    path('api/user/enable/<int:pk>', views_api.enableUser),

    path('api/device/add_device', views_api.addDevice),
    path('api/device/update_coordinates', views_api.updateDeviceCoordinates),
    path('api/device/get_all_nfc_tags', views_api.getAllNFCTags),

    path('api/device/unregistered/search', views_api.searchUnregisteredDevice),    
    path('api/device/registered/search', views_api.searchRegisteredDevice),
    path('api/device/search_by_org', views_api.searchDeviceByOrganization),
    path('api/device/delete/<int:pk>', views_api.deleteDevice),    
    path('api/device/disable/<int:pk>', views_api.disableDevice),    
    path('api/device/enable/<int:pk>', views_api.enableDevice),    
    path('api/device/delete_from_org/<int:pk>', views_api.deleteDeviceFromOrg),    

    path('api/location/search', views_api.searchLocation),
    path('api/location/search_by_postcode', views_api.searchLocationByPostCode),
    path('api/location/delete/<int:pk>', views_api.deleteLocation),

    path('api/group/search', views_api.searchGroup),
    path('api/group/delete/<int:pk>', views_api.deleteGroup),

    path('api/mail_template/get_content/<int:pk>', views_api.getMailTemplateContent),

    path('api/log/check_for_update', views_api.checkForNewLogs),
    path('api/log/mark_all_as_read', views_api.markAllLogsAsRead),
    path('api/log/search', views_api.searchLog),
]