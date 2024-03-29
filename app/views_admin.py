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
from .mail_utils import sendResellerInvitationMail, sendAdminInvitationMail
from .log_utils import logAction

# ========================================== Resellers ======================================================

@login_required
def listResellers(request):
    if not request.user.is_superuser:
        return redirect('login')

    return render(request, "_admin/resellers/list.html")

@login_required
def addReseller(request):
    if not request.user.is_superuser:
        return redirect('login')

    form = ResellerCreateForm()

    if request.method == 'POST':
        form = ResellerCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']            

            password = genPassword()
            user = User.objects.create_user(username=email, password='temp_' + password)
            user.fullname = fullname
            user.email = email
            user.status = User.Status.INVITED
            user.isReseller = True
            user.createdDate = timezone.now()
            user.save()
            
            sendResellerInvitationMail(fullname, email, password)
                
            logAction('CREATE', request.user, None, user)
            return redirect('admin-home')

    return render(request, '_admin/resellers/form.html', {'form': form})

@login_required
def resendResellerMail(request, pk):
    if not request.user.is_superuser:
        return redirect('login')

    reseller = get_object_or_404(User, pk=pk)

    if reseller and reseller.status == User.Status.INVITED:
        password = genPassword()
        reseller.password = make_password('temp_' + password)
        reseller.save()
        sendResellerInvitationMail(reseller.fullname, reseller.email, password)
    
    return redirect('admin-home')


# ========================================== Organization ======================================================
def createTenantAdmin(request, organization, adminName, adminEmail):
    if adminEmail == "":
        return 

    password = genPassword()
    user = User()
    user.username = user.email = adminEmail
    user.password = make_password('temp_' + password)
    user.fullname = adminName    
    user.status = User.Status.INVITED
    user.createdDate = timezone.now()
    user.organization = organization    
    
    user.save()
    user.roles.add(Role.objects.get(code='ADMIN'))
    user.save()

    logAction('CREATE', request.user, None, user)
    sendAdminInvitationMail(organization.name, adminName, adminEmail, password)


@login_required
def listOrganizations(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    return render(request, "_admin/organizations/list.html")

@login_required
def viewOrganizationDetails(request, pk):
    if not request.user.is_superuser and not request.user.isReseller:
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
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')
    org = get_object_or_404(Organization, pk=pk)
    return render(request, "_admin/organizations/list_users.html", {"organization": org})

@login_required
def addOrganization(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    form = OrganizationCreationForm(initial={'nfcEnabled': True, 'active': True})

    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.createdDate = timezone.now()
            org.createdBy = request.user
            org.adminUsername = form.cleaned_data['adminEmail']
            org.save()
            
            logAction('CREATE', request.user, None, org)

            adminEmail = form.cleaned_data['adminEmail']
            adminName = form.cleaned_data['adminName']

            createTenantAdmin(request, org, adminName, adminEmail)

            return redirect('admin-organization')

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    old_org = get_object_or_404(Organization, pk=pk)
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationChangeForm(instance=org)

    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST, instance=org)
        if form.is_valid():                        
            org = form.save(commit=True)
            logAction('UPDATE', request.user, old_org, org)
            return redirect('admin-organization')

    return render(request, '_admin/organizations/form.html', {'form': form})

@login_required
def resendAdminMail(request, pk):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    org = get_object_or_404(Organization, pk=pk)
    tenantAdmin = User.objects.filter(username=org.adminUsername).first()
    if tenantAdmin and tenantAdmin.status == User.Status.INVITED:
        password = genPassword()
        tenantAdmin.password = make_password('temp_' + password)
        tenantAdmin.save()
        sendAdminInvitationMail(org.name, tenantAdmin.fullname, tenantAdmin.email, password)
    
    return redirect('admin-organization')
    
ORG_HEADER = [_('name'), _('admin.name'), _('admin.email'), _('active')]

@login_required
def exportOrganization(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    lst = Organization.objects.all()
    with open('organizations.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(ORG_HEADER)
        for item in lst:
            tenantAdmin = User.objects.filter(username=item.adminUsername).first()
            adminName = tenantAdmin.fullname if tenantAdmin else ''
            adminEmail = tenantAdmin.email if tenantAdmin else ''
            writer.writerow([item.name, adminName, adminEmail, item.active])

    csv_file = open('organizations.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'
    return response

@login_required
def importOrganizationPreview(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    return importPreview(request, ORG_HEADER)

@login_required
def importOrganization(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    if request.method == 'POST':
        records = request.session.get("records", [])
        indexes = [0] * len(ORG_HEADER)
        
        for i in range(len(indexes)):
            indexes[i] = int(request.POST.get(f'col_{i}', '0'))
        
        for row in records:
            name, adminName, adminEmail, active = getPermutation(row, indexes)
            if Organization.objects.filter(name=name).count() > 0:
                continue

            org = Organization()
            org.name = name
            org.adminUsername = adminEmail
            org.active = active == 'True'
            org.createdDate = timezone.now()
            org.save()

            createTenantAdmin(request, org, adminName, adminEmail)
        
        del request.session['records']
    
    return redirect('admin-organization')

# ========================================== Unregistered devices ==========================================

@login_required
def listUnregisteredDevices(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    return render(request, "_admin/devices/unregistered/list.html")

@login_required
def addUnregisteredDevice(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    form = UnRegisteredDeviceForm()

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST)
        if form.is_valid():            
            device = form.save(commit=False)
            device.createdDate = timezone.now()
            device.createdBy = request.user
            device.status = Device.Status.ENABLED           
            device.enabled = True 
            device.save()
            logAction('CREATE', request.user, None, device)
            return redirect('admin-unregistered-device')

    return render(request, '_admin/devices/unregistered/form.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    if not request.user.is_superuser and not request.user.isReseller:
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
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    device = get_object_or_404(Device, pk=pk)
    logAction('DELETE', request.user, device, None)
    device.delete()
    return redirect("admin-unregistered-device")

DEVICE_HEADER = [_('id1'), _('id2')]

@login_required
def exportUnregisteredDevice(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    lst = Device.objects.filter(organization__isnull=True)
    
    if request.user.isReseller:
        lst = lst.filter(createdBy=request.user)

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
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    return importPreview(request, DEVICE_HEADER)

@login_required
def importUnregisteredDevice(request):
    if not request.user.is_superuser and not request.user.isReseller:
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
            device.createdDate = timezone.now()
            device.createdBy = request.user
            device.save()
        
        del request.session['records']
    
    return redirect('admin-unregistered-device')

# ========================================== Registered devices ==========================================

@login_required
def listRegisteredDevices(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    return render(request, "_admin/devices/registered/list.html")

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
    if not request.user.is_superuser:
        return redirect('login')

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

# ========================================== Logs ==========================================            

@login_required
def listLogs(request):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    actions = LogAction.objects.all()
    logConfigs = LogConfig.objects.all()
    modelNames = [logConfig.modelName for logConfig in logConfigs]
    
    organizations = Organization.objects.all()
    if not request.user.is_superuser:
        organizations = organizations.filter(createdBy=request.user)

    context = {
        'actions': actions,
        'organizations': organizations,
        'modelNames': modelNames
    }
    return render(request, '_admin/logs/list.html', context)

@login_required
def viewLogDetail(request, pk):
    if not request.user.is_superuser and not request.user.isReseller:
        return redirect('login')

    log = get_object_or_404(Log, pk=pk)
    logConfig = LogConfig.objects.filter(modelName=log.modelName).first()
    logFields = logConfig.logFields.split(',') if logConfig and logConfig.logFields else []
    preContent = json.loads(log.preContent) if log.preContent else {}
    postContent = json.loads(log.postContent) if log.postContent else {}

    if request.user not in log.viewUsers.all():
        log.viewUsers.add(request.user)
        log.save()

    return render(request, '_admin/logs/details.html', 
            {
                'log':log, 
                'logFields': logFields,
                'preContent': preContent,
                'postContent': postContent
            })    