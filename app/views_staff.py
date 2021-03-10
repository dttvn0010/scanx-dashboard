from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils import timezone
from django.template.defaulttags import register
from django.utils.translation import gettext_lazy as _

import csv
import json
from datetime import datetime, timedelta

from .models import *
from .forms_staff import *

from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendInvitationMail, sendAdminCreateNotificationMail
from .log_utils import logAction

@register.filter
def get_item(d, key):
    val = d.get(key)
    if val == None:
        return ''
    return val

@register.filter
def has_role(user, roleCode):
    return user and user.hasRole(roleCode)

@register.filter
def has_group(user, group):
    return user and user.hasGroup(group)

@register.filter
def has_page_view_permission(user, pageCode):
    return user and user.hasPagePermission(pageCode, 'VIEW')

@register.filter
def has_page_edit_permission(user, pageCode):
    return user and user.hasPagePermission(pageCode, 'EDIT')

@register.filter
def has_page_delete_permission(user, pageCode):
    return user and user.hasPagePermission(pageCode, 'DELETE')

@register.filter
def has_feature_permission(user, featureCode):
    return user and user.hasFeaturePermission(featureCode)

@register.filter
def get_checkin_status_str(code):
    if code == CheckIn.Status.SUCCESS:
        return _('successful')
    else:
        return CheckIn.Status.messages.get(code, '')
        
@login_required
def home(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, "staff/home.html")

@login_required
def tableView(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, "staff/table_view.html")

@login_required
def mapView(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, "staff/map_view.html")

def createTempUser(request, fullname, email):
    if email == "":
        return 

    password = genPassword()
    user = User.objects.create_user(username=email, password='temp_' + password)
    user.fullname = fullname
    user.email = email
    user.status = User.Status.INVITED
    user.createdDate = timezone.now()
    user.organization = request.user.organization
    user.save()
    
    sendInvitationMail(user.organization.name, fullname, email, password)

    return user


# ========================================== Users======================================================

@login_required
def listUsers(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, "staff/users/list.html")

@login_required
def addUser(request):
    if not request.user.organization:
        return redirect('login')

    form = UserCreateForm(initial={'nfcEnabled': True, 'sharedLocation': True})
    allRoles = Role.objects.all()
    roleAdmin = allRoles.filter(code='ADMIN').first()
    allGroups = Group.objects.filter(organization=request.user.organization)

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']            
            user = createTempUser(request,  fullname, email)
            user.nfcEnabled = form.cleaned_data['nfcEnabled']
            user.sharedLocation = form.cleaned_data['sharedLocation']
            roleIds = form.cleaned_data.get('roleIds', '')
            
            for roleId in roleIds.split(','):
                user.roles.add(Role.objects.get(pk=roleId))

            groupIds = form.cleaned_data.get('groupIds', '')
            for groupId in groupIds.split(','):
                if groupId:
                    user.groups.add(Group.objects.get(pk=groupId))

            user.save()
            
            if user.is_tenant_admin:
                adminUsers = User.objects.filter(organization=request.user.organization, roles__code='ADMIN')
                for adminUser in adminUsers:
                    if adminUser.username == user.username:
                        continue
                    sendAdminCreateNotificationMail(adminUser.fullname, adminUser.email, user.fullname, user.email)
                
            logAction('CREATE', request.user, None, user)
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', {
        'form': form, 
        'allRoles': allRoles, 
        'roleAdmin': roleAdmin,
        'allGroups': allGroups
        })

@login_required
def updateUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    old_user = get_object_or_404(User, pk=pk)
    user = get_object_or_404(User, pk=pk)
    
    form = UserChangeForm(instance=user)
    allRoles = Role.objects.all()    
    roleAdmin = allRoles.filter(code='ADMIN').first()
    allGroups = Group.objects.filter(organization=request.user.organization)

    lockAdmin = request.user.username == user.username and user.hasRole('ADMIN')

    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)        
        if form.is_valid():
            user = form.save(commit=False)
            roleIds = form.cleaned_data.get('roleIds', '')
            user.roles.clear()
            
            for roleId in roleIds.split(','):
                user.roles.add(Role.objects.get(pk=roleId))

            groupIds = form.cleaned_data.get('groupIds', '')
            user.groups.clear()
            
            for groupId in groupIds.split(','):
                if groupId:
                    user.groups.add(Group.objects.get(pk=groupId))

            user.save()
            form.save_m2m()

            logAction('UPDATE', request.user, old_user, user)
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', 
        {
            'form': form, 'edit_user': user, 'lockAdmin': lockAdmin,
            'allRoles': allRoles, 'roleAdmin': roleAdmin,
            'allGroups': allGroups
        })

@login_required
def deleteUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
    logAction('DELETE', request.user, user, None)
    user.delete()
    return redirect("staff-user")

USER_HEADER = ['Full Name', 'Email', 'Role', 'NFC Enabled', 'QR Scan Enabled', 'Location Shared']

@login_required
def exportUser(request):
    if not request.user.organization:
        return redirect('login')

    lst = User.objects.all()
    with open('users.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(USER_HEADER)
        for item in lst:
            roles = '|'.join([role.code for role in item.roles.all()])
            writer.writerow([item.fullname, item.email, roles, item.nfcEnabled, item.sharedLocation])

    csv_file = open('users.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    return response

@login_required
def importUserPreview(request):
    if not request.user.organization:
        return redirect('login')

    return importPreview(request, USER_HEADER)

@login_required
def importUser(request):
    if not request.user.organization:
        return redirect('login')

    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(USER_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            fullname, email, roles, nfcEnabled, sharedLocation  = getPermutation(row, indexes)
            if User.objects.filter(email=email).count() > 0 or User.objects.filter(fullname=fullname).count() > 0:
                continue

            user = createTempUser(request, fullname, email)
            
            for role in roles.split('|'):
                user.roles.add(Role.objects.get(code=role))

            user.nfcEnabled = nfcEnabled == 'True'
            user.sharedLocation = sharedLocation == 'True'
            user.save()

        del request.session['records']
    
    return redirect('staff-user')

@login_required
def resendMail(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
    if user.organization and user.status == User.Status.INVITED:
        password = genPassword()
        user.password = make_password('temp_' + password)
        user.save()
        sendInvitationMail(user.organization.name, user.fullname, user.email, password)
    
    return redirect('staff-user')

#================================= Locations  ====================================================================
@login_required
def listLocations(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, "staff/locations/list.html")

@login_required
def addLocation(request):
    if not request.user.organization:
        return redirect('login')

    form = LocationForm()

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.createdDate = timezone.now()
            location.organization = request.user.organization
            location.save()
            logAction('CREATE', request.user, None, location)
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

@login_required
def updateLocation(request, pk):
    if not request.user.organization:
        return redirect('login')

    old_location = get_object_or_404(Location, pk=pk)
    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(instance=location)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():            
            location = form.save()
            logAction('UPDATE', request.user, old_location, location)
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

LOCATION_HEADER = ['Address Line 1', 'Address Line 2', 'City', 'Postcode']

@login_required
def exportLocation(request):
    if not request.user.organization:
        return redirect('login')

    lst = Location.objects.all()
    with open('location.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(LOCATION_HEADER)
        for item in lst:
            writer.writerow([item.addressLine1, item.addressLine2, item.city, item.postCode])

    csv_file = open('location.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="location.csv"'
    return response

@login_required
def importLocationPreview(request):
    if not request.user.organization:
        return redirect('login')

    return importPreview(request, LOCATION_HEADER)

def parseFloat(st):
    try:
        return float(st)
    except ValueError:
        pass

@login_required
def importLocation(request):
    if not request.user.organization:
        return redirect('login')

    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(LOCATION_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            addressLine1, addressLine2, city, postCode = row
            
            if Location.objects.filter(postCode=postCode).count() > 0:
                continue
            
            location = Location()
            location.addressLine1 = addressLine1
            location.addressLine2 = addressLine2
            location.postCode = postCode
            location.city = city
            location.organization = request.user.organization
            location.createdDate = timezone.now()
            location.save()
            logAction('CREATE', request.user, None, location)
        
        del request.session['records']
    
    return redirect('staff-location')

#================================= Devices  ====================================================================


@login_required
def listDevices(request):
    if not request.user.organization:
        return redirect('login')

    devices = Device.objects.filter(organization=request.user.organization)
    return render(request, "staff/devices/list.html", {"devices": devices})

def tryParseFloat(s):
    try:
        return float(s)
    except:
        return None

@login_required
def addDevice(request):
    if not request.user.organization:
        return redirect('login')

    form = DeviceCreateForm(organization=request.user.organization)

    if request.method == 'POST':
        form = DeviceCreateForm(request.POST, organization=request.user.organization)
        if form.is_valid():            
            id1 = form.cleaned_data['id1']
            id2 = form.cleaned_data['id2']
            
            old_device = Device.objects.filter(id1=id1).filter(id2=id2).first()
            device = Device.objects.filter(id1=id1).filter(id2=id2).first()
            if device:
                device.installationLocation = form.cleaned_data['installationLocation']
                device.description = form.cleaned_data['description']
                device.organization = request.user.organization
                device.registeredDate = timezone.now()                
                device.save()
                logAction('UPDATE', request.user, old_device, device)

            return redirect('staff-device')

    return render(request, 'staff/devices/form.html', {'form': form})

@login_required
def updateDevice(request, pk):
    if not request.user.organization:
        return redirect('login')

    old_device = get_object_or_404(Device, pk=pk)
    device = get_object_or_404(Device, pk=pk)
    form = DeviceChangeForm(organization=request.user.organization, 
            initial={'installationLocation': device.installationLocation, 'description': device.description})

    if request.method == 'POST':
        form = DeviceChangeForm(request.POST, organization=request.user.organization)

        if form.is_valid():
            device.installationLocation = form.cleaned_data['installationLocation']
            device.description = form.cleaned_data['description']            
            device.save()
            logAction('UPDATE', request.user, old_device, device)
            return redirect('staff-device')

    return render(request, 'staff/devices/form.html', {'form': form, 'edit_device': device})

#================================= Groups  ====================================================================

@login_required
def listGroups(request):
    if not request.user.organization:
        return redirect('login')

    groups = Group.objects.filter(organization=request.user.organization)
    return render(request, "staff/groups/list.html", {"groups": groups})

def getGroupPermissionContext(group, request):
    group_features = GroupFeaturePermission.objects.filter(group=group) if group else []
    group_page_permissions = GroupPagePermission.objects.filter(group=group) if group else []
    group_view_history_groups = GroupViewHistoryPermission.objects.filter(group=group) if group else []
    
    pages = [dict(p) for p in settings.PAGES]
    
    for group_page_permission in group_page_permissions:
        page = next(x for x in pages if x['code'] == group_page_permission.pageCode)
        if not page: continue
        page[group_page_permission.actionCode.lower()] = True

    features = [dict(f) for f in (settings.FEATURES)]
    for group_feature in group_features:
        feature = next(x for x in features if x['code'] == group_feature.featureCode)
        if not feature: continue
        feature['access'] = True

    feature = next(x for x in features if x['code'] == 'USE_APP')
    if feature and not group:
        feature['access'] = True

    viewed_groups = Group.objects.filter(organization=request.user.organization)
    for group_view_history_group in group_view_history_groups:
        viewed_group = next(x for x in viewed_groups if x.id == group_view_history_group.viewGroup.id)
        if not viewed_group: continue
        viewed_group.viewed = True

    if group:
        viewed_groups = [x for x in viewed_groups if x.id != group.id]
        
    return {
        'viewed_groups': viewed_groups,
        'pages': pages,
        'features': features,
    }

def deleteOldGroupPermissions(group):
    group_features = GroupFeaturePermission.objects.filter(group=group)
    group_page_permissions = GroupPagePermission.objects.filter(group=group)
    group_view_history_groups = GroupViewHistoryPermission.objects.filter(group=group)

    for group_feature in group_features:
        group_feature.delete()

    for group_page_permission in group_page_permissions:
        group_page_permission.delete()

    for group_view_history_group in group_view_history_groups:
        group_view_history_group.delete()

def saveGroupPermissions(group, request):

    data = request.POST
    
    features = [dict(f) for f in (settings.FEATURES)]

    for feature in features:
        featureCode = feature['code']
        if data.get('feature_' + featureCode):
            group_feature = GroupFeaturePermission(group=group, featureCode=featureCode)
            group_feature.save()

    pages = [dict(p) for p in settings.PAGES]

    for page in pages:
        pageCode = page['code']
        for action in settings.PAGE_ACTIONS:
            actionCode = action['code']
            if data.get(f'page_{pageCode}_{actionCode}'):
                group_page_permission = GroupPagePermission(group=group, pageCode=pageCode, actionCode=actionCode)
                group_page_permission.save()

    viewed_groups = Group.objects.filter(organization=request.user.organization)

    for viewed_group in viewed_groups:
        if data.get(f'viewed_group_{viewed_group.id}'):
            group_view_history_group = GroupViewHistoryPermission(group=group, viewGroup=viewed_group)
            group_view_history_group.save()


@login_required
def addGroup(request):
    if not request.user.organization:
        return redirect('login')

    form = GroupForm()
    context = getGroupPermissionContext(None, request)

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():     
            group = form.save(commit=False)
            group.organization = request.user.organization
            group.save()
            saveGroupPermissions(group, request)
            logAction('CREATE', request.user, None, group)
            return redirect('staff-group')
    
    context['form'] = form
    return render(request, 'staff/groups/form.html', context)

@login_required
def updateGroup(request, pk):
    if not request.user.organization:
        return redirect('login')

    old_group = get_object_or_404(Group, pk=pk)
    group = get_object_or_404(Group, pk=pk)
    context = getGroupPermissionContext(group, request)
    form = GroupForm(instance=group)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)

        if form.is_valid():
            group = form.save()
            deleteOldGroupPermissions(group)
            saveGroupPermissions(group, request)
            logAction('UPDATE', request.user, old_group, group)
            return redirect('staff-group')

    context['form'] = form
    return render(request, 'staff/groups/form.html', context)

#================================= Reports  ====================================================================

def getCheckInReport(users, status, userId, locationId, startDate, endDate):
    checkIns = CheckIn.objects.filter(user__in=users)

    if status == 1:
        checkIns = checkIns.filter(status=CheckIn.Status.SUCCESS)
    elif status == 2:
        checkIns = checkIns.filter(~Q(status=CheckIn.Status.SUCCESS))    

    if userId:
        checkIns = checkIns.filter(user__id=int(userId))

    if locationId:
        checkIns = checkIns.filter(location__id=int(locationId))

    if startDate:
        startDate = datetime.strptime(startDate, '%d/%m/%Y')
        checkIns = checkIns.filter(date__gte=startDate)

    if endDate:
        endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1)
        checkIns = checkIns.filter(date__lt=endDate)                        

    checkIns = checkIns.order_by('-date')

    return checkIns

@login_required
def reportCheckIn(request):
    if not request.user.organization:
        return redirect('login')

    query_params = request.GET
    reported = query_params.get('reported', '')
    
    status = query_params.get('status')
    status = int(status) if status else None

    userId = query_params.get('userId')
    userId = int(userId) if userId else  None

    locationId = query_params.get('locationId')
    locationId = int(locationId) if locationId else None

    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    users = request.user.viewed_users
    locations = Location.objects.filter(organization=request.user.organization)
    checkIns = getCheckInReport(users, status, userId, locationId, startDate, endDate)

    return render(request, 'staff/reports/check_in.html', 
        {
            'users': users, 
            'locations': locations,
            'reported': reported,
            'userId': userId,
            'status': status,
            'locationId': locationId,
            'startDate': startDate,
            'endDate': endDate,
            'checkIns': checkIns
        })

@login_required
def reportCheckInExportPdf(request):
    if not request.user.organization:
        return redirect('login')

    query_params = request.GET
    userId = query_params.get('userId')
    locationId = query_params.get('locationId')

    status = query_params.get('status')
    status = int(status) if status else None

    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    reportedUser = User.objects.get(pk=userId) if userId else None
    reportedLocation = Location.objects.get(pk=locationId) if locationId else None

    users = request.user.viewed_users
    checkIns = getCheckInReport(users, status, userId, locationId, startDate, endDate)
    resp = render(request, 'staff/reports/check_in_pdf.html', 
                {
                    'checkIns': checkIns, 
                    'date': timezone.now(),
                    'startDate': startDate,
                    'endDate': endDate,
                    'reportedUser': reportedUser,
                    'reportedLocation': reportedLocation
                })
    content = resp.content.decode()

    return HttpResponse(json.dumps({'html': content}), content_type='application/json')

def getLogInReport(users, startDate, endDate):
    logIns = LogIn.objects.filter(user__in=users)

    if startDate:
        startDate = datetime.strptime(startDate, '%d/%m/%Y')
        logIns = logIns.filter(date__gte=startDate)

    if endDate:
        endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1)
        logIns = logIns.filter(date__lt=endDate)                        

    return logIns.order_by('-date')

@login_required
def reportLogIn(request):
    if not request.user.organization:
        return redirect('login')

    query_params = request.GET
    reported = query_params.get('reported', '')
    userId = query_params.get('userId')
    userId = int(userId) if userId else None

    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    users = request.user.viewed_users
    reportedUser = User.objects.get(pk=userId) if userId else None

    logIns = getLogInReport([reportedUser] if reportedUser else users, startDate, endDate)

    return render(request, 'staff/reports/log_in.html', 
        {
            'users': users,
            'reported': reported,
            'userId': userId,
            'startDate': startDate,
            'endDate': endDate,
            'logIns': logIns
        })    

@login_required
def reportLogInExportPdf(request):  
    if not request.user.organization:
        return redirect('login')

    query_params = request.GET
    userId = query_params.get('userId')
    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    users = request.user.viewed_users

    reportedUser = User.objects.get(pk=userId) if userId else None
    logIns = getLogInReport([reportedUser] if reportedUser else users, startDate, endDate)

    resp =  render(request, 'staff/reports/log_in_pdf.html', {
                'logIns': logIns,
                'date': timezone.now(),
                'startDate': startDate,
                'endDate': endDate,
                'reportedUser': reportedUser
            })

    content = resp.content.decode()

    return HttpResponse(json.dumps({'html': content}), content_type='application/json')

#================================= Settings  ====================================================================

def configureOranization(request):
    if not request.user.organization:
        return redirect('login')

    org = request.user.organization
    initial = {'name': org.name, 'description': org.description, 'nfcEnabled': org.nfcEnabled}

    form = OrganizationChangeForm(initial=initial)
    saved = False
    
    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST)
        if form.is_valid():
            org.name = form.cleaned_data.get("name")
            org.description = form.cleaned_data.get("description")
            org.nfcEnabled = form.cleaned_data.get("nfcEnabled")
            org.save()
            saved = True

    return render(request, 'staff/settings/organization.html', {'form': form, 'saved': saved})

def appInfo(request):
    if not request.user.organization:
        return redirect('login')

    return render(request, 'staff/app_link.html')    

def createTenantParams(organization):
    params = SystemParameter.objects.filter(customizedByTenants=True)
    
    for param in params:
        existed = TenantParameter.objects.filter(organization=organization, parameter=param).count() > 0
        if not existed:
            TenantParameter(organization=organization, parameter=param, value=param.value).save()

@login_required
def editCustomParams(request):
    if not request.user.organization:
        return redirect('login')

    createTenantParams(request.user.organization)
    tenant_params = TenantParameter.objects.filter(organization=request.user.organization, parameter__customizedByTenants=True)
    tenant_param_map = {p.parameter.key:p for p in tenant_params}

    saved = False
    
    if request.method == 'POST':
        keys = [key for key in request.POST if key in tenant_param_map]

        for key in keys:
            value = request.POST[key]
            tenant_param = tenant_param_map[key]
            tenant_param.value = value
            tenant_param.save()
            
        saved = True

    return render(request, "staff/settings/tenant_params.html", 
                                {"tenant_params": tenant_params, "saved": saved})     


#================================= Logs  ====================================================================
@login_required
def listLogs(request):
    if not request.user.organization:
        return redirect('login')

    actions = LogAction.objects.all()
    logConfigs = LogConfig.objects.all()
    modelNames = [logConfig.modelName for logConfig in logConfigs]
        
    users = request.user.viewed_users

    context = {
        'actions': actions,
        'users': users,
        'modelNames': modelNames
    }
    return render(request, 'staff/logs/list.html', context)

@login_required
def viewLogDetail(request, pk):
    if not request.user.organization:
        return redirect('login')

    log = get_object_or_404(Log, pk=pk)
    logConfig = LogConfig.objects.filter(modelName=log.modelName).first()
    logFields = logConfig.logFields.split(',') if logConfig and logConfig.logFields else []
    preContent = json.loads(log.preContent) if log.preContent else {}
    postContent = json.loads(log.postContent) if log.postContent else {}

    if request.user not in log.viewUsers.all():
        log.viewUsers.add(request.user)
        log.save()

    return render(request, 'staff/logs/details.html', 
            {
                'log':log, 
                'logFields': logFields,
                'preContent': preContent,
                'postContent': postContent
            })    