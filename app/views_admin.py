from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.conf import settings

import csv
import json
from datetime import datetime
from threading import Thread

from .models import *
from .forms_admin import *

from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendAdminInvitationMail

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
    user.role = Role.objects.get(code=settings.ROLES['ADMIN'])
    user.save()

    sendAdminInvitationMail(organization.name, adminName, adminEmail, password)

# ========================================== Organization ======================================================

@login_required
def listOrganizations(request):
    if not request.user.is_superuser:
        return redirect('login')

    return render(request, "_admin/organizations/list.html")

@login_required
def listOrganizationUsers(request, pk):
    if not request.user.is_superuser:
        return redirect('login')
    org = get_object_or_404(Organization, pk=pk)
    return render(request, "_admin/organizations/list_users.html", {"organization": org})

@login_required
def addOrganization(request):
    if not request.user.is_superuser:
        return redirect('login')

    form = OrganizationCreationForm(initial={'nfcEnabled': True, 'qrScanEnabled': True, 'active': True})

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

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationChangeForm(instance=org)

    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def resendMail(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    org = get_object_or_404(Organization, pk=pk)
    tenantAdmin = User.objects.filter(username=org.adminUsername).fist()
    if tenantAdmin and tenantAdmin.status == User.Status.INVITED:
        password = genPassword()
        tenantAdmin.password = make_password('temp_' + password)
        tenantAdmin.save()
        sendAdminInvitationMail(org.name, tenantAdmin.fullname, tenantAdmin.email, password)
    
    return redirect('admin-home')
    

ORG_HEADER = ['Name', 'Admin Name', 'Admin Email', 'NFC Enabled', 'QR Scan Enabled', 'Active']

@login_required
def exportOrganization(request):
    if not request.user.is_superuser:
        return redirect('login')

    lst = Organization.objects.all()
    with open('organizations.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(ORG_HEADER)
        for item in lst:
            tenantAdmin = User.objects.filter(username=org.adminUsername).first()
            adminName = tenantAdmin.fullname if tenantAdmin else ''
            adminEmail = tenantAdmin.email if tenantAdmin else ''
            writer.writerow([item.name, adminName, adminEmail, item.nfcEnabled, item.qrScanEnabled, item.active])

    csv_file = open('organizations.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'
    return response

@login_required
def importOrganizationPreview(request):
    if not request.user.is_superuser:
        return redirect('login')

    return importPreview(request, ORG_HEADER)

@login_required
def importOrganization(request):
    if not request.user.is_superuser:
        return redirect('login')

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

# ========================================== Unregistered devices ==========================================

@login_required
def listUnregisteredDevices(request):
    if not request.user.is_superuser:
        return redirect('login')

    devices = Device.objects.filter(organization__isnull=True)
    return render(request, "_admin/devices/unregistered/list.html", {"devices": devices})

@login_required
def addUnregisteredDevice(request):
    if not request.user.is_superuser:
        return redirect('login')

    form = UnRegisteredDeviceForm()

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST)
        if form.is_valid():            
            device = form.save(commit=False)
            device.createdDate = datetime.now()
            device.enabled = True
            device.save()
            return redirect('admin-unregistered-device')

    return render(request, '_admin/devices/unregistered/form.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    device = get_object_or_404(Device, pk=pk)
    form = UnRegisteredDeviceForm(instance=device)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST, instance=device)

        if form.is_valid():
            form.save()
            return redirect('admin-unregistered-device')

    return render(request, '_admin/devices/unregistered/form.html', {'form': form})

@login_required
def deleteUnregisteredDevice(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-unregistered-device")

DEVICE_HEADER = ['ID #1', 'ID #2']

@login_required
def exportUnregisteredDevice(request):
    if not request.user.is_superuser:
        return redirect('login')

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
    if not request.user.is_superuser:
        return redirect('login')

    return importPreview(request, DEVICE_HEADER)

@login_required
def importUnregisteredDevice(request):
    if not request.user.is_superuser:
        return redirect('login')

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
def listRegisteredDevices(request):
    if not request.user.is_superuser:
        return redirect('login')

    devices = Device.objects.filter(organization__isnull=False)
    return render(request, "_admin/devices/registered/list.html", {"devices": devices})


# ========================================== Settings ==========================================

@login_required
def editAdminMailTemplate(request):
    if not request.user.is_superuser:
        return redirect('login')

    with open(settings.ADMIN_MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
        admin_mail_template = fi.read()

    saved = False

    if request.method == 'POST':
        admin_mail_template = request.POST["admin_mail_template"]
        with open(settings.ADMIN_MAIL_TEMPLATE_PATH, 'w', encoding="utf-8", newline="") as fo:
            fo.write(admin_mail_template.replace("\n\n", "\n"))
            saved = True        
    
    return render(request, "_admin/settings/admin_mail_template.html", 
            {"admin_mail_template": admin_mail_template, "saved": saved})   

@login_required
def editMailTemplate(request):
    if not request.user.is_superuser:
        return redirect('login')

    with open(settings.MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
        mail_template = fi.read()

    saved = False

    if request.method == 'POST':
        mail_template = request.POST["mail_template"]
        with open(settings.MAIL_TEMPLATE_PATH, 'w', encoding="utf-8", newline="") as fo:
            fo.write(mail_template.replace("\n\n", "\n"))
            saved = True        
    
    return render(request, "_admin/settings/mail_template.html", 
            {"mail_template": mail_template, "saved": saved})    

@login_required
def editSystemParams(request):
    if not request.user.is_superuser:
        return redirect('login')

    params = Parameter.objects.all()

    saved = False

    if request.method == 'POST':
        for key in request.POST:
            value = request.POST[key]
            for p in params:
                if p.key == key:                    
                    p.value = value

        for param in params:
            param.save()
            
        saved = True

    return render(request, "_admin/settings/system_params.html", 
                                {"params": params, "saved": saved}) 