from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from django.contrib.auth.decorators import login_required

import csv
from datetime import datetime
from threading import Thread

from .models import *
from .forms_admin import *

from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendAdminInvitationMail
from .permissions import PERMISSIONS
from .consts import MAIL_TEMPLATE_PATH, ADMIN_MAIL_TEMPLATE_PATH

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

# ========================================== Organization ======================================================

@login_required
def listOrganization(request):
    return render(request, "_admin/organization/list.html")

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
            return redirect('admin-organization')

    return render(request, '_admin/organization/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationChangeForm(instance=org)

    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, '_admin/organization/form.html', {'form': form})

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

#================================= Permission ====================================================================
@login_required
def listPermission(request):
    return render(request, "_admin/permission/list.html")

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

    return render(request, '_admin/permission/form.html', 
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

    return render(request, '_admin/permission/form.html', 
                {'form': form, 'details': getPermissionDetail(permission)})


# ========================================== Unregistered devices ==========================================

@login_required
def listUnregisteredDevice(request):
    devices = Device.objects.filter(organization__isnull=True)
    return render(request, "_admin/device/unregistered/list.html", {"devices": devices})

@login_required
def addUnregisteredDevice(request):
    form = UnRegisteredDeviceForm()

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST)
        if form.is_valid():            
            device = form.save(commit=False)
            device.createdDate = datetime.now()
            device.enabled = True
            device.save()
            return redirect('admin-unregistered-device')

    return render(request, '_admin/device/unregistered/form.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = UnRegisteredDeviceForm(instance=device)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST, instance=device)

        if form.is_valid():
            form.save()
            return redirect('admin-unregistered-device')

    return render(request, '_admin/device/unregistered/form.html', {'form': form})

@login_required
def deleteUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-unregistered-device")

DEVICE_HEADER = ['ID #1', 'ID #2']

@login_required
def exportUnregisteredDevice(request):
    lst = Device.objects.filter(organization__isnull=True)
    with open('unreg_devices.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(DEVICE_HEADER)
        for item in lst:
            writer.writerow([item.id1, item.id2])

    csv_file = open('unreg_devices.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="unreg_devices.csv"'
    return response

@login_required
def importUnregisteredDevicePreview(request):
    return importPreview(request, DEVICE_HEADER)

@login_required
def importUnregisteredDevice(request):
    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(DEVICE_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            id1, id2 = row

            if Device.objects.filter(id1=id1).filter(id2=id2).count() > 0:
                continue
            
            device = Device()
            device.id1 = id1
            device.id2 = id2
            device.enabled = True
            device.save()
        
        del request.session['records']
    
    return redirect('admin-unregistered-device')

# ========================================== Registered devices ==========================================

@login_required
def listRegisteredDevice(request):
    devices = Device.objects.filter(organization__isnull=False)
    return render(request, "_admin/device/registered/list.html", {"devices": devices})


# ========================================== Settings ==========================================

@login_required
def editMailTemplate(request):
    with open(ADMIN_MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
        email_template = fi.read()

    saved = False

    if request.method == 'POST':
        email_template = request.POST["email_template"]
        with open(ADMIN_MAIL_TEMPLATE_PATH, 'w', encoding="utf-8", newline="") as fo:
            fo.write(email_template.replace("\n\n", "\n"))
            saved = True        
    
    return render(request, "_admin/settings/mail_template.html", 
            {"email_template": email_template, "saved": saved})    