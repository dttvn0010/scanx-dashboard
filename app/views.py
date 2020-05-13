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

from .models import *
from .forms import *
from .consts import MAIL_TEMPLATE_PATH
from .mail_utils import sendInvitationMail
from datetime import datetime
import string
import random
import csv
import json
from multiprocessing import Process
import traceback

TMP_PATH = 'tmp'
fs = FileSystemStorage()

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/admins")
    else:
        if(request.user.status == User.Status.INVITED):
            return HttpResponseRedirect("/complete_registration")
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

            return HttpResponseRedirect("/users")

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

# User
@login_required
def userViewTable(request):
    return render(request, "users/table_view.html")

@login_required
def userViewMap(request):
    return render(request, "users/map_view.html")

# Admin
@login_required
def adminViewOrganization(request):
    organizations = Organization.objects.all()
    for org in organizations:
        staff = User.objects.filter(organization=org).filter(is_staff=True).first()
        org.admin = staff
        org.userCount = User.objects.filter(organization=org).count()
        org.deviceCount = Device.objects.filter(organization=org).count()

    with open(MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
        email_template = fi.read()

    return render(request, "admins/organization/list.html", 
                    {"organizations" : organizations, "email_template": email_template})

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
    #print('Sending email:' , hostURL, adminName, adminEmail, password)
    #proc = Process(target=sendInvitationMail, args=(hostURL, organization.name, adminName, adminEmail, password))
    #proc.start() 
    try:
        sendInvitationMail(hostURL, organization.name, adminName, adminEmail, password)
    except:
        traceback.print_exc()

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

@login_required
def deleteOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    org.delete()
    return redirect("admin-home")

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
