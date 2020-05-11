import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.core.files.storage import FileSystemStorage
from .models import *
from .forms import *
import csv
from datetime import datetime

TMP_PATH = 'tmp'
fs = FileSystemStorage()

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/admins")
    else:
        return HttpResponseRedirect("/users")

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

    return render(request, "admins/organization/list.html", {"organizations" : organizations})

@login_required
def addOrganization(request):
    form = OrganizationForm()

    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(instance=org)

    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

@login_required
def deleteOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    org.delete()
    return redirect("admin-home")

ORG_HEADER = ['Name', 'Description', 'Date Time Format', 'NFC Enabled', 'QR Scan Enabled', 'Active']

@login_required
def exportOrganization(request):
    lst = Organization.objects.all()
    with open('organizations.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(ORG_HEADER)
        for item in lst:
            writer.writerow([item.name, item.description, item.dateTimeFormat, item.nfcEnabled, item.qrScanEnabled, item.active])

    csv_file = open('organizations.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'
    return response

@login_required
def importOrganization(request):
    if request.method == 'POST':
        csvFile = request.FILES.get('csv_file')
        if csvFile and csvFile.name:
            tmpFilePath = os.path.join(TMP_PATH, csvFile.name)
            savedPath = fs.save(tmpFilePath, csvFile)

            with open(savedPath) as fi:
                reader = csv.reader(fi)
                header = next(reader)
                if header == ORG_HEADER:
                    for row in reader:
                        name, description, dateTimeFormat, nfcEnabled, qrScanEnabled, active = row
                        if Organization.objects.filter(name=name).count() > 0:
                            continue

                        org = Organization()
                        org.name = name
                        org.description = description
                        org.dateTimeFormat = dateTimeFormat
                        org.nfcEnabled = nfcEnabled == 'True'
                        org.qrScanEnabled = qrScanEnabled == 'True'
                        org.active = active == 'True'
                        org.save()
                
            os.remove(savedPath)
        
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
            writer.writerow([item.id1, item.id2, item.deviceType.name, item.deviceGroup.name,
                            postCode, item.locationDescription, item.enabled])

    csv_file = open('unreg_devices.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="unreg_devices.csv"'
    return response

@login_required
def importUnregisteredDevice(request):
    if request.method == 'POST':
        csvFile = request.FILES.get('csv_file')
        if csvFile and csvFile.name:
            tmpFilePath = os.path.join(TMP_PATH, csvFile.name)
            savedPath = fs.save(tmpFilePath, csvFile)

            with open(savedPath) as fi:
                reader = csv.reader(fi)
                header = next(reader)
                if header == UNREGISTERED_DEVICE_HEADER:                        
                    for row in reader:
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
            
            os.remove(savedPath)
        
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
            writer.writerow([item.id1, item.id2, item.deviceType.name, item.deviceGroup.name,
                        postCode, item.locationDescription, 
                        item.registeredDate.strftime('%Y-%m-%d'),
                        '' if not item.organization else item.organization.name,
                        item.enabled])

    csv_file = open('reg_devices.csv', 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="reg_devices.csv"'
    return response

@login_required
def importRegisteredDevice(request):
    if request.method == 'POST':
        csvFile = request.FILES.get('csv_file')
        if csvFile and csvFile.name:
            tmpFilePath = os.path.join(TMP_PATH, csvFile.name)
            savedPath = fs.save(tmpFilePath, csvFile)

            with open(savedPath) as fi:
                reader = csv.reader(fi)
                header = next(reader)
                if header == REGISTERED_DEVICE_HEADER:                        
                    for row in reader:                        
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
                        device.registeredDate = datetime.strptime(registeredDate, '%Y-%m-%d')
                        device.enabled = enabled == 'True'
                        device.status = Device.Status.REGISTERED
                        device.save()
            
            os.remove(savedPath)
        
    return redirect('admin-registered-device')    