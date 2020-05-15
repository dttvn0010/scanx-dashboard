import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login, authenticate

from datetime import datetime
import string
import random
import csv
import json
from threading import Thread

from .models import *
from .forms import *
from .consts import MAIL_TEMPLATE_PATH
from .mail_utils import sendAdminInvitationMail, sendInvitationMail
from .permissions import PERMISSIONS


TMP_PATH = 'tmp'
fs = FileSystemStorage()

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/admins")
    else:
        if(request.user.status == User.Status.INVITED):
            return HttpResponseRedirect("/complete_registration")
        elif request.user.is_staff:
            return HttpResponseRedirect("/staff")
        else:
            return HttpResponseRedirect("/users")

@login_required
def completeRegistration(request):
    form = MyUserRegistrationForm(initial={
            'fullname': request.user.fullname, 
            'organization': request.user.organization.name
        })

    if request.method == 'POST':
        form = MyUserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.fullname = form.cleaned_data['fullname']
            user.password = make_password(form.cleaned_data['password'])
            user.status = User.Status.REGISTERED
            user.profilePicture = form.cleaned_data['profilePicture']
            user.save()

            org = user.organization
            org.name = form.cleaned_data['organization']
            org.save()

            user = authenticate(username=user.username,
                                    password=form.cleaned_data['password'])
            login(request, user)

            return HttpResponseRedirect("/")

    return render(request, "registration/complete.html", {'form': form})

def signup(request):
   form = MyUserCreationForm()
   
   if request.method == 'POST':
       form = MyUserCreationForm(request.POST)
       if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username,
                                    password=request.POST['password1'])
            login(request, user)
            return redirect('home')

   return render(request, 'registration/signup.html', { 'form':  form})

#Users
def userHome(request):
    return render(request, "users/index.html")

# Staff
@login_required
def staffViewTable(request):
    return render(request, "staff/table_view.html")

@login_required
def staffViewMap(request):
    return render(request, "staff/map_view.html")

def genPassword():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def createTenantAdmin(request, organization, adminName, adminEmail):
    if adminEmail == "":
        return 

    password = genPassword()
    user = User.objects.create_user(username=adminEmail, password=password)
    user.fullname = adminName
    user.email = adminEmail
    user.status = User.Status.INVITED
    user.createdDate = datetime.now()
    user.organization = organization
    user.is_staff = True
    user.save()

    hostURL = request.build_absolute_uri('/')    
    thr = Thread(target=sendAdminInvitationMail, args=(hostURL, organization.name, adminName, adminEmail, password))
    thr.start()

def createUser(request, organization, fullname, email):
    if email == "":
        return 

    password = genPassword()
    user = User.objects.create_user(username=email, password=password)
    user.fullname = fullname
    user.email = email
    user.status = User.Status.INVITED
    user.createdDate = datetime.now()
    user.organization = organization
    user.save()
    
    hostURL = request.build_absolute_uri('/')        
    thr = Thread(target=sendInvitationMail, args=(hostURL, organization.name, fullname, email, password))
    thr.start()

    return user

def getPermutation(row, indexes):
    return [row[i] for i in indexes]

def importPreview(request, header):
    if request.method == 'POST':
        csvFile = request.FILES.get('csv_file')
        if csvFile and csvFile.name:
            tmpFilePath = os.path.join(TMP_PATH, csvFile.name)
            savedPath = fs.save(tmpFilePath, csvFile)

            with open(savedPath) as fi:
                reader = csv.reader(fi)
                csvHeader = next(reader)
                records = list(reader)
                request.session['records'] = records
                
            os.remove(savedPath)
            
            return HttpResponse(json.dumps({"header": header, "csvHeader": csvHeader}), 
                        content_type='application/json')

    else:
        return HttpResponse(json.dumps({"error": "Method not support"}), 
                    content_type='application/json')

# ========================================== Organization ======================================================

@login_required
def adminViewOrganization(request):
    return render(request, "admins/organization/list.html")

@login_required
def addOrganization(request):
    form = OrganizationCreationForm()

    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.createdDate = datetime.now()
            org.save()

            adminEmail = form.cleaned_data['adminEmail']
            adminName = form.cleaned_data['adminName']

            createTenantAdmin(request, org, adminName, adminEmail)
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationChangeForm(instance=org)

    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

ORG_HEADER = ['Name', 'Admin Name', 'Admin Email', 'NFC Enabled', 'QR Scan Enabled', 'Active']

@login_required
def exportOrganization(request):
    lst = Organization.objects.all()
    with open('organizations.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(ORG_HEADER)
        for item in lst:
            staff = User.objects.filter(organization=item).filter(is_staff=True).first()
            adminName = staff.fullname if staff else ''
            adminEmail = staff.email if staff else ''
            writer.writerow([item.name, adminName, adminEmail, item.nfcEnabled, item.qrScanEnabled, item.active])

    csv_file = open('organizations.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'
    return response

@login_required
def importOrganizationPreview(request):
    return importPreview(request, ORG_HEADER)

@login_required
def importOrganization(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(ORG_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            name, adminName, adminEmail, nfcEnabled, qrScanEnabled, active = getPermutation(row, indexes)
            if Organization.objects.filter(name=name).count() > 0:
                continue

            org = Organization()
            org.name = name
            org.nfcEnabled = nfcEnabled == 'True'
            org.qrScanEnabled = qrScanEnabled == 'True'
            org.active = active == 'True'
            org.createdDate = datetime.now()
            org.save()

            createTenantAdmin(request, org, adminName, adminEmail)
        
        del request.session['records']
    
    return redirect('admin-home')

# ========================================== User ======================================================
@login_required
def adminViewUser(request):
    return render(request, "admins/user/list.html")

@login_required
def addUser(request):
    form = UserForm()

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']
            org = form.cleaned_data['organization']

            createUser(request, org, fullname, email)
            return redirect('admin-user')

    return render(request, 'admins/user/form.html', {'form': form})

@login_required
def updateUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin-user')

    return render(request, 'admins/user/form.html', {'form': form})

@login_required
def deleteUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return redirect("admin-user")

USER_HEADER = ['Full name', 'Email', 'Organization', 'NFC Enabled', 'QR Scan Enabled', 'Location Shared']

@login_required
def exportUser(request):
    lst = User.objects.all()
    with open('users.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(USER_HEADER)
        for item in lst:
            organizationName = item.organization.name if item.organization else ''
            writer.writerow([item.fullname, item.email, organizationName,
                                 item.nfcEnabled, item.qrScanEnabled, item.sharedLocation])

    csv_file = open('users.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    return response

@login_required
def importUserPreview(request):
    return importPreview(request, USER_HEADER)

@login_required
def importUser(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(USER_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            fullname, email, organizationName, nfcEnabled, qrScanEnabled, sharedLocation  = getPermutation(row, indexes)
            if User.objects.filter(email=email).count() > 0 or User.objects.filter(fullname=fullname).count() > 0:
                continue

            organization = Organization.objects.filter(name=organizationName).first()
            user = createUser(request, organization, fullname, email)
            user.nfcEnabled = nfcEnabled == 'True'
            user.qrScanEnabled = qrScanEnabled == 'True'
            user.sharedLocation = sharedLocation == 'True'
            user.save()

        del request.session['records']
    
    return redirect('admin-user')

#================================= Permission ====================================================================
@login_required
def adminViewPermission(request):
    return render(request, "admins/permission/list.html")

def splitToIntArr(st):
    if st:
        arr = st.split(',')
        return [int(x) for x in arr]

    return []

def getPermissionDetail(permission):
    if not permission:
        return [{'permission': p['name']} for p in PERMISSIONS]
        
    details = {}
    accessFunctions = splitToIntArr(permission.accessFunctions)
    viewFunctions = splitToIntArr(permission.viewFunctions)
    editFunctions = splitToIntArr(permission.editFunctions)
    deleteFunctions = splitToIntArr(permission.deleteFunctions)
    
    safe_get = lambda arr, i : arr[i] if i < len(arr) else 0

    return [
        {
            'permission': PERMISSIONS[i]['name'],
            'access': safe_get(accessFunctions,i),
            'view': safe_get(viewFunctions,i),
            'edit': safe_get(editFunctions,i),
            'delete': safe_get(deleteFunctions,i),
        }
        for i in range(len(PERMISSIONS))
    ]


@login_required
def addPermission(request):
    form = PermissionForm()

    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            permission = form.save(commit=False)
            permission.createdDate = datetime.now()
            permission.save()
            return redirect('admin-permission')

    return render(request, 'admins/permission/form.html', 
            {'form': form, 'details': getPermissionDetail(None)})

@login_required
def updatePermission(request, pk):
    permission = get_object_or_404(Permission, pk=pk)
    form = PermissionForm(instance=permission)

    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            return redirect('admin-permission')

    return render(request, 'admins/permission/form.html', 
                {'form': form, 'details': getPermissionDetail(permission)})

#================================= Device Type ====================================================================
@login_required
def adminViewDeviceType(request):
    return render(request, "admins/device_type/list.html")

@login_required
def addDeviceType(request):
    form = DeviceTypeForm()

    if request.method == 'POST':
        form = DeviceTypeForm(request.POST)
        if form.is_valid():
            deviceType = form.save(commit=False)
            deviceType.createdDate = datetime.now()
            deviceType.save()
            return redirect('admin-device-type')

    return render(request, 'admins/device_type/form.html', {'form': form})

@login_required
def updateDeviceType(request, pk):
    deviceType = get_object_or_404(DeviceType, pk=pk)
    form = DeviceTypeForm(instance=deviceType)

    if request.method == 'POST':
        form = DeviceTypeForm(request.POST, instance=deviceType)
        if form.is_valid():
            form.save()
            return redirect('admin-device-type')

    return render(request, 'admins/device_type/form.html', {'form': form})

DEVICE_TYPE_HEADER = ['Name', 'Description', 'Organization']

@login_required
def exportDeviceType(request):
    lst = DeviceType.objects.all()
    with open('device_type.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(DEVICE_TYPE_HEADER)
        for item in lst:
            organizationName = item.organization.name if item.organization else ''
            writer.writerow([item.name, item.description, organizationName])

    csv_file = open('device_type.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="device_type.csv"'
    return response

@login_required
def importDeviceTypePreview(request):
    return importPreview(request, DEVICE_TYPE_HEADER)

@login_required
def importDeviceType(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(DEVICE_TYPE_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            name, description, organizationName = row
           
            if DeviceType.objects.filter(name=name).count() > 0:
                continue
            
            deviceType = DeviceType()
            deviceType.name = name
            deviceType.description = description
            deviceType.organization = Organization.objects.filter(name=organizationName).first()
            deviceType.save()
        
        del request.session['records']
    
    return redirect('admin-device-type')


#================================= Device Group====================================================================
@login_required
def adminViewDeviceGroup(request):
    return render(request, "admins/device_group/list.html")

@login_required
def addDeviceGroup(request):
    form = DeviceGroupForm()

    if request.method == 'POST':
        form = DeviceGroupForm(request.POST)
        if form.is_valid():
            deviceGroup = form.save(commit=False)
            deviceGroup.createdDate = datetime.now()
            deviceGroup.save()
            return redirect('admin-device-group')

    return render(request, 'admins/device_group/form.html', {'form': form})

@login_required
def updateDeviceGroup(request, pk):
    deviceGroup = get_object_or_404(DeviceGroup, pk=pk)
    form = DeviceGroupForm(instance=deviceGroup)

    if request.method == 'POST':
        form = DeviceGroupForm(request.POST, instance=deviceGroup)
        if form.is_valid():
            form.save()
            return redirect('admin-device-group')

    return render(request, 'admins/device_group/form.html', {'form': form})

DEVICE_GROUP_HEADER = ['Name', 'Description', 'Organization']

@login_required
def exportDeviceGroup(request):
    lst = DeviceGroup.objects.all()
    with open('device_group.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(DEVICE_GROUP_HEADER)
        for item in lst:
            organizationName = item.organization.name if item.organization else ''
            writer.writerow([item.name, item.description, organizationName])

    csv_file = open('device_group.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="device_group.csv"'
    return response

@login_required
def importDeviceGroupPreview(request):
    return importPreview(request, DEVICE_GROUP_HEADER)

@login_required
def importDeviceGroup(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(DEVICE_GROUP_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            name, description, organizationName = row
           
            if DeviceGroup.objects.filter(name=name).count() > 0:
                continue
            
            deviceGroup = DeviceGroup()
            deviceGroup.name = name
            deviceGroup.description = description
            deviceGroup.organization = Organization.objects.filter(name=organizationName).first()
            deviceGroup.save()
        
        del request.session['records']
    
    return redirect('admin-device-group')

# ========================================== Unregistered devices ==========================================

@login_required
def adminViewUnregisteredDevice(request):
    devices = Device.objects.filter(status=Device.Status.UNREGISTERED)
    return render(request, "admins/device/list_unregistered.html", {"devices": devices})

@login_required
def addUnregisteredDevice(request):
    form = UnRegisteredDeviceForm(organization=request.user.organization)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST)
        if form.is_valid():            
            device = form.save(commit=False)
            device.status = Device.Status.UNREGISTERED
            device.createdDate = datetime.now()
            device.save()
            return redirect('admin-unregistered-device')

    return render(request, 'admins/device/form_unregistered.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = UnRegisteredDeviceForm(instance=device, organization=request.user.organization)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST, instance=device, organization=request.user.organization)

        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.UNREGISTERED
            device.save()            
            return redirect('admin-unregistered-device')

    return render(request, 'admins/device/form_unregistered.html', {'form': form})

@login_required
def deleteUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-unregistered-device")

UNREGISTERED_DEVICE_HEADER = ['ID #1', 'ID #2', 'Device Type', 'Device Group', 'Installation Location',
                                'Location Description', 'Enabled']

@login_required
def exportUnregisteredDevice(request):
    lst = Device.objects.filter(status=Device.Status.UNREGISTERED)
    with open('unreg_devices.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(UNREGISTERED_DEVICE_HEADER)
        for item in lst:
            postCode = item.installationLocation.postCode if item.installationLocation else ''
            deviceType = item.deviceType.name if item.deviceType else ''
            deviceGroup = item.deviceGroup.name if item.deviceGroup else ''
            writer.writerow([item.id1, item.id2, deviceType, deviceGroup,
                            postCode, item.locationDescription, item.enabled])

    csv_file = open('unreg_devices.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="unreg_devices.csv"'
    return response


@login_required
def importUnregisteredDevicePreview(request):
    return importPreview(request, UNREGISTERED_DEVICE_HEADER)

@login_required
def importUnregisteredDevice(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(UNREGISTERED_DEVICE_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            id1, id2, deviceTypeName, deviceGroupName, postCode, locationDescription, enabled = row

            if Device.objects.filter(id1=id1).filter(id2=id2).count() > 0:
                continue
            
            device = Device()
            device.id1 = id1
            device.id2 = id2
            device.deviceType = DeviceType.objects.filter(name=deviceTypeName).first()
            device.deviceGroup = DeviceGroup.objects.filter(name=deviceGroupName).first()
            device.installationLocation = Location.objects.filter(postCode=postCode).first()
            device.locationDescription = locationDescription
            device.enabled = enabled == 'True'
            device.status = Device.Status.UNREGISTERED
            device.save()
        
        del request.session['records']
    
    return redirect('admin-unregistered-device')

@login_required
def adminViewRegisteredDevice(request):
    devices = Device.objects.filter(status=Device.Status.REGISTERED)
    return render(request, "admins/device/list_registered.html", {"devices": devices})

@login_required
def addRegisteredDevice(request):
    form = RegisteredDeviceForm()

    if request.method == 'POST':
        form = RegisteredDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.REGISTERED
            device.createdDate = datetime.now()
            device.save()   
            return redirect('admin-registered-device')

    return render(request, 'admins/device/form_registered.html', {'form': form})

@login_required
def updateRegisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = RegisteredDeviceForm(instance=device)

    if request.method == 'POST':
        form = RegisteredDeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.REGISTERED
            device.save()
            return redirect('admin-registered-device')

    return render(request, 'admins/device/form_registered.html', {'form': form})

@login_required
def deleteRegisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-registered-device")

REGISTERED_DEVICE_HEADER = ['ID #1', 'ID #2', 'Device Type', 'Device Group', 'Installation Location',
                                'Location Description', 'Registered Date', 'Organization', 'Enabled']

@login_required
def exportRegisteredDevice(request):
    lst = Device.objects.filter(status=Device.Status.REGISTERED)
    with open('reg_devices.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(REGISTERED_DEVICE_HEADER)
        for item in lst:
            postCode = item.installationLocation.postCode if item.installationLocation else ''
            deviceType = item.deviceType.name if item.deviceType else ''
            deviceGroup = item.deviceGroup.name if item.deviceGroup else ''

            writer.writerow([item.id1, item.id2, deviceType, deviceGroup,
                        postCode, item.locationDescription, 
                        item.registeredDate.strftime('%d %b,%Y'),
                        '' if not item.organization else item.organization.name,
                        item.enabled])

    csv_file = open('reg_devices.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="reg_devices.csv"'
    return response

@login_required
def importRegisteredDevicePreview(request):
    return importPreview(request, REGISTERED_DEVICE_HEADER)

@login_required
def importRegisteredDevice(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(REGISTERED_DEVICE_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            id1, id2, deviceTypeName, deviceGroupName, postCode, locationDescription, registeredDate, organizationName, enabled = row

            if Device.objects.filter(id1=id1).filter(id2=id2).count() > 0:
                continue
            
            device = Device()
            device.id1 = id1
            device.id2 = id2
            device.deviceType = DeviceType.objects.filter(name=deviceTypeName).first()
            device.deviceGroup = DeviceGroup.objects.filter(name=deviceGroupName).first()
            device.installationLocation = Location.objects.filter(postCode=postCode).first()
            device.locationDescription = locationDescription
            device.organization = Organization.objects.filter(name=organizationName).first()
            device.registeredDate = datetime.strptime(registeredDate, "%d %b,%Y")
            device.enabled = enabled == 'True'
            device.status = Device.Status.REGISTERED
            device.save()
        
        del request.session['records']
    
    return redirect('admin-registered-device')

#================================= Location Group====================================================================
@login_required
def adminViewLocationGroup(request):
    return render(request, "admins/location_group/list.html")

@login_required
def addLocationGroup(request):
    form = LocationGroupForm()

    if request.method == 'POST':
        form = LocationGroupForm(request.POST)
        if form.is_valid():
            locationGroup = form.save(commit=False)
            locationGroup.createdDate = datetime.now()
            locationGroup.save()
            return redirect('admin-location-group')

    return render(request, 'admins/location_group/form.html', {'form': form})

@login_required
def updateLocationGroup(request, pk):
    locationGroup = get_object_or_404(LocationGroup, pk=pk)
    form = LocationGroupForm(instance=locationGroup)

    if request.method == 'POST':
        form = LocationGroupForm(request.POST, instance=locationGroup)
        if form.is_valid():
            form.save()
            return redirect('admin-location-group')

    return render(request, 'admins/location_group/form.html', {'form': form})

LOCATION_GROUP_HEADER = ['Name', 'Description', 'Organization']

@login_required
def exportLocationGroup(request):
    lst = LocationGroup.objects.all()
    with open('location_group.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(LOCATION_GROUP_HEADER)
        for item in lst:
            organizationName = item.organization.name if item.organization else ''
            writer.writerow([item.name, item.description, organizationName])

    csv_file = open('location_group.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="location_group.csv"'
    return response

@login_required
def importLocationGroupPreview(request):
    return importPreview(request, LOCATION_GROUP_HEADER)

@login_required
def importLocationGroup(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(LOCATION_GROUP_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            name, description, organizationName = row
           
            if LocationGroup.objects.filter(name=name).count() > 0:
                continue
            
            locationGroup = LocationGroup()
            locationGroup.name = name
            locationGroup.description = description
            locationGroup.organization = Organization.objects.filter(name=organizationName).first()
            locationGroup.save()
        
        del request.session['records']
    
    return redirect('admin-location-group')


#================================= Location  ====================================================================
@login_required
def adminViewLocation(request):
    return render(request, "admins/location/list.html")

@login_required
def addLocation(request):
    form = LocationForm()

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.createdDate = datetime.now()
            location.save()
            return redirect('admin-location')

    return render(request, 'admins/location/form.html', {'form': form})

@login_required
def updateLocation(request, pk):
    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(instance=location)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('admin-location')

    return render(request, 'admins/location/form.html', {'form': form})

LOCATION_HEADER = ['Address Line 1', 'Address Line 2', 'Postcode', 'Location Group', 'Organization', 'Google Location']

@login_required
def exportLocation(request):
    lst = Location.objects.all()
    with open('location.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(LOCATION_HEADER)
        for item in lst:
            locationGroup = item.locationGroup.name if item.locationGroup else ''
            organizationName = item.organization.name if item.organization else ''
            writer.writerow([item.addressLine1, item.addressLine2, item.postCode,
                        locationGroup, organizationName, item.geoLocation])

    csv_file = open('location.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="location.csv"'
    return response

@login_required
def importLocationPreview(request):
    return importPreview(request, LOCATION_HEADER)

def parseFloat(st):
    try:
        return float(st)
    except ValueError:
        pass

@login_required
def importLocation(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(LOCATION_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:                        
            addressLine1, addressLine2, postCode, locationGroup, organizationName, geoLocation = row
            
            if Location.objects.filter(postCode=postCode).count() > 0:
                continue
            
            location = Location()
            location.addressLine1 = addressLine1
            location.addressLine2 = addressLine2
            location.postCode = postCode
            location.locationGroup = LocationGroup.objects.filter(name=locationGroup).first()
            location.organization = Organization.objects.filter(name=organizationName).first()
            location.geoLocation = geoLocation
            location.save()
        
        del request.session['records']
    
    return redirect('admin-location')

#===================================================================================================================

@login_required
def editMailTemplate(request):
    with open(MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
        email_template = fi.read()

    saved = False

    if request.method == 'POST':
        email_template = request.POST["email_template"]
        with open(MAIL_TEMPLATE_PATH, 'w', encoding="utf-8", newline="") as fo:
            fo.write(email_template.replace("\n\n", "\n"))
            saved = True        
    
    return render(request, "admins/settings/mail_template.html", 
            {"email_template": email_template, "saved": saved})
