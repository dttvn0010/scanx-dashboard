from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone

import csv
import json
from datetime import datetime
from threading import Thread

from .models import *
from .forms_admin import *

from .param_utils import getSystemParamValue
from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendAdminInvitationMail
from .log_utils import logAction

def createTenantAdmin(request, organization, adminName, adminEmail):
    if adminEmail == "":
        return 

    password = genPassword()
    user = User()
    user.username = user.email = adminEmail
    user.password = make_password('temp_' + password)
    user.fullname = adminName    
    user.nfcEnabled =  user.sharedLocation = True
    user.qrScanEnabled = False
    user.status = User.Status.INVITED
    user.createdDate = timezone.now()
    user.organization = organization    
    
    user.save()
    user.roles.add(Role.objects.get(code=settings.ROLES['ADMIN']))
    user.save()

    logAction('CREATE', request.user, None, user)
    sendAdminInvitationMail(organization.name, adminName, adminEmail, password)

# ========================================== Organization ======================================================

@login_required
def listOrganizations(request):
    if not request.user.is_superuser:
        return redirect('login')

    return render(request, "_admin/organizations/list.html")

@login_required
def viewOrganizationDetails(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    org = get_object_or_404(Organization, pk=pk)
    tenantAdmin = User.objects.filter(username=org.adminUsername).first()
    users = User.objects.filter(organization=org).order_by('createdDate')
    devices = Device.objects.filter(organization=org)
    locations = Location.objects.filter(organization=org)

    return render(request, "_admin/organizations/details.html",
        {
            "organization": org,
            "tenantAdmin": tenantAdmin,
            "users": users,
            "locations": locations,
            "devices": devices
        })

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

    form = OrganizationCreationForm(initial={'nfcEnabled': True, 'qrScanEnabled': False, 'active': True})

    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.createdDate = timezone.now()
            org.adminUsername = form.cleaned_data['adminEmail']
            org.save()
            
            logAction('CREATE', request.user, None, org)

            adminEmail = form.cleaned_data['adminEmail']
            adminName = form.cleaned_data['adminName']

            createTenantAdmin(request, org, adminName, adminEmail)

            return redirect('admin-home')

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    old_org = get_object_or_404(Organization, pk=pk)
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationChangeForm(instance=org)

    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST, instance=org)
        if form.is_valid():                        
            org = form.save(commit=True)
            logAction('UPDATE', request.user, old_org, org)
            return redirect('admin-home')

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def resendMail(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    org = get_object_or_404(Organization, pk=pk)
    tenantAdmin = User.objects.filter(username=org.adminUsername).first()
    if tenantAdmin and tenantAdmin.status == User.Status.INVITED:
        password = genPassword()
        tenantAdmin.password = make_password('temp_' + password)
        tenantAdmin.save()
        sendAdminInvitationMail(org.name, tenantAdmin.fullname, tenantAdmin.email, password)
    
    return redirect('admin-home')
    

ORG_HEADER = [_('name'), _('admin.name'), _('admin.email'), _('nfc.enabled'), _('qr.scanning.enabled'), _('active')]

@login_required
def exportOrganization(request):
    if not request.user.is_superuser:
        return redirect('login')

    lst = Organization.objects.all()
    with open('organizations.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(ORG_HEADER)
        for item in lst:
            tenantAdmin = User.objects.filter(username=item.adminUsername).first()
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
            org.adminUsername = adminEmail
            org.nfcEnabled = nfcEnabled == 'True'
            org.qrScanEnabled = qrScanEnabled == 'True'
            org.active = active == 'True'
            org.createdDate = timezone.now()
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
            device.createdDate = timezone.now()
            device.status = Device.Status.ENABLED            
            device.save()
            logAction('CREATE', request.user, None, device)
            return redirect('admin-unregistered-device')

    return render(request, '_admin/devices/unregistered/form.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    old_device = get_object_or_404(Device, pk=pk)
    device = get_object_or_404(Device, pk=pk)
    form = UnRegisteredDeviceForm(instance=device)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST, instance=device)

        if form.is_valid():            
            device = form.save()
            logAction('UPDATE', request.user, old_device, device)
            return redirect('admin-unregistered-device')

    return render(request, '_admin/devices/unregistered/form.html', {'form': form})

@login_required
def deleteUnregisteredDevice(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    device = get_object_or_404(Device, pk=pk)
    logAction('DELETE', request.user, device, None)
    device.delete()
    return redirect("admin-unregistered-device")

DEVICE_HEADER = [_('id1'), _('id2')]

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
def editSystemParams(request):
    if not request.user.is_superuser:
        return redirect('login')

    params = SystemParameter.objects.all()
    param_map = {p.key: p for p in params}

    saved = False

    if request.method == 'POST':
        keys = [key for key in request.POST if key in param_map]

        for key in keys:
            param = param_map[key]
            value = request.POST[key]
            param.value = value
            param.save()

        saved = True

    return render(request, "_admin/settings/system_params.html", 
                                {"params": params, "saved": saved}) 

def editMailTemplates(request):    
    saved = False
    template_id = subject = body = ''
    form = MailTemplateChangeForm()
    
    if request.method == 'POST':
        form = MailTemplateChangeForm(request.POST)
        if form.is_valid():
            template_id = form.cleaned_data.get('template_id')
            template = MailTemplate.objects.filter(pk=template_id).first()
            if template:
                subject = template.subject = form.cleaned_data.get('subject')
                body = template.body = form.cleaned_data.get('body')
                template.save()
                saved = True

    return render(request, "_admin/settings/mail_templates.html", 
            {
                'templates': MailTemplate.objects.all(), 
                'saved': saved, 
                'subject': subject, 
                'body': body, 
                'template_id': template_id
            }) 