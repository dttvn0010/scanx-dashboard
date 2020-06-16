from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

import csv
import json
from datetime import datetime, timedelta
from threading import Thread

from .models import *
from .forms_staff import *

from .user_utils import genPassword
from .import_utils import getPermutation, importPreview
from .mail_utils import sendInvitationMail

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
    user.createdDate = datetime.now()
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

    form = UserCreateForm(initial={'nfcEnabled': True, 'qrScanEnabled': True, 'sharedLocation': True})

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']            
            user = createTempUser(request,  fullname, email)
            user.nfcEnabled = form.cleaned_data['nfcEnabled']
            user.qrScanEnabled = form.cleaned_data['qrScanEnabled']
            user.sharedLocation = form.cleaned_data['sharedLocation']
            user.role = pk=form.cleaned_data['role']
            user.save()
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', {'form': form})

@login_required
def updateUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
    
    if user.role.code != 'ADMIN' and user.username == request.user.username:
        form = UserAdminChangeForm(instance=user)
    else:
        form = UserChangeForm(instance=user)

    if request.method == 'POST':
        if user.role.code != 'ADMIN' and user.username == request.user.username:
            form = UserAdminChangeForm(request.POST, instance=user)
        else:
            form = UserChangeForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('staff-user')

    return render(request, 'staff/users/form.html', {'form': form, 'edit_user': user})

@login_required
def deleteUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
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
            role = item.role.code if item.role else ''
            writer.writerow([item.fullname, item.email, role, item.nfcEnabled, item.qrScanEnabled, item.sharedLocation])

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
            fullname, email, role, nfcEnabled, qrScanEnabled, sharedLocation  = getPermutation(row, indexes)
            if User.objects.filter(email=email).count() > 0 or User.objects.filter(fullname=fullname).count() > 0:
                continue

            user = createTempUser(request, fullname, email)
            user.role = Role.objects.get(code=role)
            user.nfcEnabled = nfcEnabled == 'True'
            user.qrScanEnabled = qrScanEnabled == 'True'
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

@login_required
def lockUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    return redirect('staff-user')

@login_required
def unlockUser(request, pk):
    if not request.user.organization:
        return redirect('login')

    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
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
            location.createdDate = datetime.now()
            location.organization = request.user.organization
            location.save()
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

@login_required
def updateLocation(request, pk):
    if not request.user.organization:
        return redirect('login')

    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(instance=location)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('staff-location')

    return render(request, 'staff/locations/form.html', {'form': form})

LOCATION_HEADER = ['Address Line 1', 'Address Line 2', 'Postcode', 'City', 'Geo Location']

@login_required
def exportLocation(request):
    if not request.user.organization:
        return redirect('login')

    lst = Location.objects.all()
    with open('location.csv', 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(LOCATION_HEADER)
        for item in lst:
            writer.writerow([item.addressLine1, item.addressLine2, item.city, item.postCode, item.geoLocation])

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
            addressLine1, addressLine2, city, postCode, geoLocation = row
            
            if Location.objects.filter(postCode=postCode).count() > 0:
                continue
            
            location = Location()
            location.addressLine1 = addressLine1
            location.addressLine2 = addressLine2
            location.postCode = postCode
            location.city = city
            location.organization = request.user.organization
            location.geoLocation = geoLocation
            location.createdDate = datetime.now()
            location.save()
        
        del request.session['records']
    
    return redirect('staff-location')

#================================= Devices  ====================================================================


@login_required
def listDevices(request):
    if not request.user.organization:
        return redirect('login')

    devices = Device.objects.filter(organization=request.user.organization)
    return render(request, "staff/devices/list.html", {"devices": devices})

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
    if not request.user.organization:
        return redirect('login')

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

#================================= Reports  ====================================================================

def getCheckInReport(organization, userId, locationId, startDate, endDate):
    checkIns = CheckIn.objects.filter(user__organization=organization)

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
    userId = query_params.get('userId', '')
    locationId = query_params.get('locationId', '')
    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    users = User.objects.filter(organization=request.user.organization)
    locations = Location.objects.filter(organization=request.user.organization)
    checkIns = getCheckInReport(request.user.organization, userId, locationId, startDate, endDate)

    return render(request, 'staff/reports/check_in.html', 
        {
            'users': users, 
            'locations': locations,
            'reported': reported,
            'userId': userId,
            'locationId': locationId,
            'startDate': startDate,
            'endDate': endDate,
            'checkIns': checkIns
        })

@login_required
def reportCheckInExportPdf(request):
    query_params = request.GET
    userId = query_params.get('userId', '')
    locationId = query_params.get('locationId', '')
    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    reportedUser = User.objects.get(pk=userId) if userId else None
    reportedLocation = Location.objects.get(pk=locationId) if locationId else None

    checkIns = getCheckInReport(request.user.organization, userId, locationId, startDate, endDate)
    resp = render(request, 'staff/reports/check_in_pdf.html', 
                {
                    'checkIns': checkIns, 
                    'date': datetime.now(),
                    'startDate': startDate,
                    'endDate': endDate,
                    'reportedUser': reportedUser,
                    'reportedLocation': reportedLocation
                })
    content = resp.content.decode()

    return HttpResponse(json.dumps({'html': content}), content_type='application/json')

def getLogInReport(organization, userId, startDate, endDate):
    logIns = LogIn.objects.filter(user__organization=organization)

    if userId:
        logIns = logIns.filter(user__id=int(userId))

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
    userId = query_params.get('userId', '')
    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    users = User.objects.filter(organization=request.user.organization)
    logIns = getLogInReport(request.user.organization, userId, startDate, endDate)

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
    query_params = request.GET
    userId = query_params.get('userId', '')
    startDate = query_params.get('startDate', '')
    endDate = query_params.get('endDate', '')

    reportedUser = User.objects.get(pk=userId) if userId else None
    logIns = getLogInReport(request.user.organization, userId, startDate, endDate)

    resp =  render(request, 'staff/reports/log_in_pdf.html', {
                'logIns': logIns,
                'date': datetime.now(),
                'startDate': startDate,
                'endDate': endDate,
                'reportedUser': reportedUser
            })

    content = resp.content.decode()

    return HttpResponse(json.dumps({'html': content}), content_type='application/json')

#================================= Settings  ====================================================================

def configureOranization(request):
    org = request.user.organization
    initial = {'name': org.name, 'nfcEnabled': org.nfcEnabled, 'qrScanEnabled': org.qrScanEnabled}
    form = OrganizationChangeForm(initial=initial)
    saved = False
    
    if request.method == 'POST':
        form = OrganizationChangeForm(request.POST)
        if form.is_valid():
            org.name = form.cleaned_data.get("name")
            org.nfcEnabled = form.cleaned_data.get("nfcEnabled")
            org.qrScanEnabled = form.cleaned_data.get("qrScanEnabled")
            org.save()
            saved = True

    return render(request, 'staff/settings/organization.html', {'form': form, 'saved': saved})

def appInfo(request):
    return render(request, 'staff/app_link.html')    