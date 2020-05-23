from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

import csv
from datetime import datetime
from threading import Thread

from .models import *
from .forms_staff import *

from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendInvitationMail

@login_required
def tableView(request):
    return render(request, "staff/table_view.html")

@login_required
def mapView(request):
    return render(request, "staff/map_view.html")

def createUser(request, fullname, email):
    if email == "":
        return 

    password = genPassword()
    user = User.objects.create_user(username=email, password=password)
    user.fullname = fullname
    user.email = email
    user.status = User.Status.INVITED
    user.createdDate = datetime.now()
    user.organization = request.user.organization
    user.save()
    
    hostURL = request.build_absolute_uri('/')        
    sendInvitationMail(hostURL, user.organization.name, fullname, email, password)
    #thr = Thread(target=sendInvitationMail, args=(hostURL, user.organization.name, fullname, email, password))
    #thr.start()

    return user


# ========================================== User ======================================================
@login_required
def listUser(request):
    return render(request, "staff/users/list.html")

@login_required
def addUser(request):
    form = UserCreateForm(initial={'nfcEnabled': True, 'qrScanEnabled': True, 'sharedLocation': True})

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']            
            user = createUser(request,  fullname, email)
            user.nfcEnabled = form.cleaned_data['nfcEnabled']
            user.qrScanEnabled = form.cleaned_data['qrScanEnabled']
            user.sharedLocation = form.cleaned_data['sharedLocation']
            user.save()
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', {'form': form})

@login_required
def updateUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserChangeForm(instance=user)

    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', {'form': form, 'edit_user': user})

@login_required
def deleteUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return redirect("staff-user")

USER_HEADER = ['Full Name', 'Email', 'NFC Enabled', 'QR Scan Enabled', 'Location Shared']

@login_required
def exportUser(request):
    lst = User.objects.all()
    with open('users.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(USER_HEADER)
        for item in lst:
            writer.writerow([item.fullname, item.email, item.nfcEnabled, item.qrScanEnabled, item.sharedLocation])

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
            fullname, email, nfcEnabled, qrScanEnabled, sharedLocation  = getPermutation(row, indexes)
            if User.objects.filter(email=email).count() > 0 or User.objects.filter(fullname=fullname).count() > 0:
                continue

            user = createUser(request, fullname, email)
            user.nfcEnabled = nfcEnabled == 'True'
            user.qrScanEnabled = qrScanEnabled == 'True'
            user.sharedLocation = sharedLocation == 'True'
            user.save()

        del request.session['records']
    
    return redirect('staff-user')

@login_required
def resendMail(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.organization and user.status == User.Status.INVITED:
        hostURL = request.build_absolute_uri('/')    
        password = genPassword()
        user.password = make_password(password)
        user.save()
        #thr = Thread(target=sendInvitationMail, args=(hostURL, user.organization.name, user.fullname, user.email, password))
        #thr.start()
        sendInvitationMail(hostURL, user.organization.name, user.fullname, user.email, password)
    
    return redirect('staff-user')

@login_required
def lockUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    return redirect('staff-user')

@login_required
def unlockUser(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    return redirect('staff-user')    

#================================= Location  ====================================================================
@login_required
def listLocation(request):
    return render(request, "staff/locations/list.html")

@login_required
def addLocation(request):
    form = LocationForm()

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.createdDate = datetime.now()
            location.organization = request.user.organization
            location.save()
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

@login_required
def updateLocation(request, pk):
    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(instance=location)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

LOCATION_HEADER = ['Address Line 1', 'Address Line 2', 'Postcode', 'Geo Location']

@login_required
def exportLocation(request):
    lst = Location.objects.all()
    with open('location.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(LOCATION_HEADER)
        for item in lst:
            writer.writerow([item.addressLine1, item.addressLine2, item.postCode, item.geoLocation])

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
            addressLine1, addressLine2, postCode, geoLocation = row
            
            if Location.objects.filter(postCode=postCode).count() > 0:
                continue
            
            location = Location()
            location.addressLine1 = addressLine1
            location.addressLine2 = addressLine2
            location.postCode = postCode
            location.organization = request.user.organization
            location.geoLocation = geoLocation
            location.createdDate = datetime.now()
            location.save()
        
        del request.session['records']
    
    return redirect('staff-location')

#================================= Device  ====================================================================


@login_required
def listDevice(request):
    devices = Device.objects.filter(organization=request.user.organization)
    return render(request, "staff/devices/list.html", {"devices": devices})

@login_required
def addDevice(request):
    form = DeviceCreateForm(organization=request.user.organization)

    if request.method == 'POST':
        form = DeviceCreateForm(request.POST, organization=request.user.organization)
        if form.is_valid():            
            id1 = form.cleaned_data['id1']
            id2 = form.cleaned_data['id2']
            installationLocation = form.cleaned_data['installationLocation']
            
            device = Device.objects.filter(id1=id1).filter(id2=id2).first()
            if device:
                device.installationLocation = installationLocation
                device.organization = request.user.organization
                device.registeredDate = datetime.now()
                device.save()

            return redirect('staff-device')

    return render(request, 'staff/devices/form.html', {'form': form})

@login_required
def updateDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = DeviceChangeForm(organization=request.user.organization, initial={'installationLocation': device.installationLocation})

    if request.method == 'POST':
        form = DeviceChangeForm(request.POST, organization=request.user.organization)

        if form.is_valid():
            installationLocation = form.cleaned_data['installationLocation']
            device.installationLocation = installationLocation
            device.save()
            return redirect('staff-device')

    return render(request, 'staff/devices/form.html', {'form': form})

@login_required
def deleteDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.organization = None
    device.installationLocation = None
    device.save()
    return redirect("staff-device")    

#================================= Report  ====================================================================

@login_required
def viewReport(request):
    return render(request, 'staff/reports/list.html')