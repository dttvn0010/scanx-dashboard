from django.db.models import Q
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from pytz import timezone

import json
import requests
import traceback
from datetime import datetime, timedelta

from .models import *
from .serializers import *

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def test(request):
    return Response({'success': True})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getUserConfig(request):
    nfcEnabled = qrScanEnabled = sharedLocation = False

    if request.user and request.user.organization:
        nfcEnabled = request.user.nfcEnabled and request.user.organization.nfcEnabled
        qrScanEnabled = request.user.qrScanEnabled and request.user.organization.qrScanEnabled
        sharedLocation = request.user.sharedLocation

    return Response({ 
        'nfcEnabled': nfcEnabled,
        'qrScanEnabled': qrScanEnabled,
        'sharedLocation': False,# sharedLocation
    })

# ================================================ LogIn ========================================================

@api_view(['POST'])
def logIn(request):
    noLogIn = settings.MOBILE_NO_LOG_IN
    headers = {'Content-type': 'application/json'}
    resp_text = requests.post(settings.HOST_URL + "/api/token", data=json.dumps(request.data), headers=headers).text    
    resp = json.loads(resp_text)
    username = request.data.get("username")

    if noLogIn and not resp.get('access'):
        username = settings.MOBILE_USERNAME
        data = {'username': username, 'password': settings.MOBILE_PASSWORD}
        resp_text = requests.post(settings.HOST_URL + "/api/token", data=json.dumps(data), headers=headers).text
        resp = json.loads(resp_text)

    if resp.get('access'):
        logIn = LogIn()
        logIn.user = User.objects.filter(username=username).first()
        logIn.date = datetime.now()
        logIn.save()
    
    return Response(resp)

@api_view(['GET'])
def searchLogIn(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')    
    userId = request.query_params.get("userId")
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")

    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    logIns = LogIn.objects.filter(user__organization=request.user.organization)
    recordsTotal = logIns.count()

    if keyword != '':
        logIns = logIns.filter(user__fullname__contains=keyword)

    if userId:
        logIns = logIns.filter(user__id=int(userId))

    if startDate:
        startDate = datetime.strptime(startDate, '%d/%m/%Y')
        logIns = logIns.filter(date__gte=startDate)

    if endDate:
        endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1)
        logIns = logIns.filter(date__lt=endDate)                        

    logIns = logIns.order_by('-date')
    recordsFiltered = logIns.count()
    logIns = logIns[start:start+length]
    data = LogInSerializer(logIns, many=True).data

    for item in data:
        item['user'] = f'{item["userFullName"]}'
        d = datetime.strptime(item['date'], "%d/%m/%Y %H:%M:%S")
        diff = datetime.now() - d
        seconds = diff.seconds + diff.days * 24 * 3600
        
        minutes = seconds // 60
        hours = seconds // 3600
        
        if hours == 0:
            item['datediff'] = f'{minutes} minute{"" if minutes == 1 else "s"}'
        else:
            item['datediff'] = f'{hours} hour{"" if hours == 1 else "s"}'

    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

# ================================================ CheckIn ========================================================

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def checkIn(request):

    code = request.data.get("code")
    position = request.data.get("position")

    arr = code.split('-')
    if len(arr) != 3 or arr[0] != "SCANX":
        pos = code.find('en')
        if pos >= 0:
            code = code[pos+2:]
        return Response({
            'success': False, 
            'error': 'Invalid device code!'
        })
    
    id1, id2 = arr[1:]
    device = Device.objects.filter(id1=id1).filter(id2=id2).first()
    if not device:
        return Response({
            'success': False, 
            'error': f'Device does not exist in device table - please contact admin!'
        })

    if not device.installationLocation:
        return Response({
            'success': False, 
            'error': f'Device is unregistered - please contact admin!'
        })

    lastCheckIn = CheckIn.objects.filter(user=request.user).order_by('-date').first()
    delayParam = Parameter.objects.filter(key='SCAN_TIME_DELAY').first()
    
    if lastCheckIn and delayParam and delayParam.value:
        minWaitTime = float(delayParam.value)
        
        if minWaitTime == int(minWaitTime):
            minWaitTime = int(minWaitTime)

        timediff = datetime.timestamp(datetime.now()) - datetime.timestamp(lastCheckIn.date)

        if timediff < minWaitTime * 60:
            return Response({
                'success': False, 
                'error': f'Please wait a minimum of {minWaitTime} minutes before next scan'
            })
        
    checkIn = CheckIn()
    checkIn.location = device.installationLocation
    checkIn.device = device
    checkIn.user = request.user
    checkIn.date = datetime.now()

    if position:
        lat = position.get("lat", "")
        lng = position.get("lng", "")
        checkIn.geoLocation = f"{lat},{lng}"
        
    checkIn.save()

    deviceId = f'{device.id1}-{device.id2}'
    location = str(device.installationLocation)

    return Response({
        'success': True, 
        'message': f'Successfully Scanned Device\nLocation is: {location}'
    })

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getLastCheckInTime(request):
    lastCheckIn = CheckIn.objects.order_by('-date').first()
    if lastCheckIn:
        lastUpdated = CheckInSerializer(lastCheckIn).data['date']
        return Response({'time': lastUpdated})
    else:
        return Response({'time': ''})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def checkForNewCheckIn(request):
    lastUpdated = request.GET.get('last_updated', '')
    updated = False

    if lastUpdated != '':
        lastUpdatedTime = datetime.strptime(lastUpdated, '%d/%m/%Y %H:%M:%S')
        lastCheckIn = CheckIn.objects.order_by('-date').first()

        if lastCheckIn:
            lastUpdated = lastCheckInDate = CheckInSerializer(lastCheckIn).data['date']
            lastCheckInDate = datetime.strptime(lastCheckInDate, '%d/%m/%Y %H:%M:%S')
            updated = lastCheckInDate > lastUpdatedTime

    return Response({'updated': updated, 'lastUpdated': lastUpdated})

@api_view(['GET'])
def searchCheckIn(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')    
    userId = request.query_params.get("userId")
    locationId = request.query_params.get("locationId")
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")
    
    mapView = request.query_params.get("mapView")
    if mapView:
        flushTimeParam = Parameter.objects.filter(key='MAP_VIEW_FLUSH_TIME').first()
        if flushTimeParam and flushTimeParam.value:
            flushTime = float(flushTimeParam.value)
            startDate = datetime.now() - timedelta(seconds=3600*flushTime)
            endDate = None
    else:
        startDate = datetime.strptime(startDate, '%d/%m/%Y') if startDate else None
        endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1) if endDate else None
        
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    checkIns = CheckIn.objects.filter(user__organization=request.user.organization)
    recordsTotal = checkIns.count()

    if keyword != '':
        checkIns = checkIns.filter(Q(user__fullname__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword))

    if userId:
        checkIns = checkIns.filter(user__id=int(userId))

    if locationId:
        checkIns = checkIns.filter(location__id=int(locationId))

    if startDate:        
        checkIns = checkIns.filter(date__gte=startDate)

    if endDate:        
        checkIns = checkIns.filter(date__lt=endDate)
        
    checkIns = checkIns.order_by('-date')
    recordsFiltered = checkIns.count()
    checkIns = checkIns[start:start+length]
    data = CheckInSerializer(checkIns, many=True).data

    for item in data:
        item['user'] = f'{item["userFullName"]}'
        item['location'] = f'{item["addressLine1"]}, {item["addressLine2"]}, {item["city"]}, {item["postCode"]}'
        
        d = datetime.strptime(item['date'], "%d/%m/%Y %H:%M:%S")
        diff = datetime.now() - d        
        seconds = diff.seconds + diff.days * 24 * 3600
        
        minutes = seconds // 60
        hours = seconds // 3600
        
        if hours == 0:
            item['datediff'] = f'{minutes} minute{"" if minutes == 1 else "s"}'
        else:
            item['datediff'] = f'{hours} hour{"" if hours == 1 else "s"}'

        arr = item['geoLocation'].split(',')
        if len(arr) == 2:
            lat = float(arr[0])
            lng = float(arr[1])
            item['geoLocation'] = {'lat': lat, 'lng': lng}

    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

# =================================================== Organization ======================================================

@api_view(['GET'])
def searchOrganization(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    organizations = Organization.objects.all()
    recordsTotal = organizations.count()

    organizations = organizations.filter(name__contains=keyword).order_by('-createdDate')
    recordsFiltered = organizations.count()
    organizations = organizations[start:start+length]
    data = OrganizationSerializer(organizations, many=True).data

    for i, org in enumerate(organizations):
        staff = User.objects.filter(organization=org).filter(role__code=settings.ROLES['ADMIN']).first()
        data[i]['admin'] = {'name': staff.fullname if staff else "", 'email': staff.email if staff else ""}
        data[i]['userCount'] = User.objects.filter(organization=org).count()
        data[i]['deviceCount'] = Device.objects.filter(organization=org).count()
        data[i]['status'] = staff.status if staff else User.Status.INVITED
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

@api_view(['GET'])
def viewOrganizationDetails(request, pk):    
    org = Organization.objects.get(pk=pk)
    data = OrganizationSerializer(org).data
    staff = User.objects.filter(organization=org).filter(role__code=settings.ROLES['ADMIN']).first()
    data['admin'] = {'name': staff.fullname if staff else "", 'email': staff.email if staff else ""}
    data['userCount'] = User.objects.filter(organization=org).count()
    data['deviceCount'] = Device.objects.filter(organization=org).count()
    data['status'] = staff.status if staff else User.Status.INVITED
    
    return Response(data)

@api_view(['POST'])
def deleteOrganization(request, pk):    
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            organization = Organization.objects.get(pk=pk)  
            organization.delete()  
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': 'Wrong password'})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

# =================================================== User ======================================================

@api_view(['GET'])
def searchUser(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    users = User.objects.filter(organization=request.user.organization)
    recordsTotal = users.count()

    users = users.filter(Q(fullname__contains=keyword) | Q(email__contains=keyword))
    users = users.order_by('role__level', '-createdDate')
    
    recordsFiltered = users.count()
    users = users[start:start+length]
    data = UserSerializer(users, many=True).data
        
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

@api_view(['GET'])
def viewUserDetails(request, pk):    
    user = User.objects.get(pk=pk)
    data = UserSerializer(user).data
    return Response(data)

@api_view(['POST'])
def deleteUser(request, pk):   
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            user = User.objects.get(pk=pk)    
            user.delete() 
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': 'Wrong password'})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

# =================================================== Device ======================================================

@api_view(['GET'])
def searchUnregisteredDevice(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    devices = Device.objects.filter(organization__isnull=True)
    recordsTotal = devices.count()

    devices = devices.filter(Q(id1__contains=keyword) | Q(id2__contains=keyword)).order_by('-createdDate')
    recordsFiltered = devices.count()
    devices = devices[start:start+length]
    data = DeviceSerializer(devices, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

@api_view(['POST'])
def deleteDevice(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            device = Device.objects.get(pk=pk)    
            device.delete()  
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': 'Wrong password'})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
def deleteDeviceFromOrg(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            device = Device.objects.get(pk=pk)
            device.organization = None
            device.installationLocation = None
            device.save()
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': 'Wrong password'})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
def searchRegisteredDevice(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    devices = Device.objects.filter(organization__isnull=False)
    recordsTotal = devices.count()

    devices = devices.filter(Q(id1__contains=keyword) | Q(id2__contains=keyword)).order_by('-createdDate')
    recordsFiltered = devices.count()
    devices = devices[start:start+length]
    data = DeviceSerializer(devices, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })    

@api_view(['GET'])
def searchDeviceByOrganization(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    devices = Device.objects.filter(organization=request.user.organization)
    recordsTotal = devices.count()

    devices = devices.filter(Q(id1__contains=keyword) | Q(id2__contains=keyword)).order_by('-createdDate')
    recordsFiltered = devices.count()
    devices = devices[start:start+length]
    data = DeviceSerializer(devices, many=True).data

    for item in data:
        item['location'] = f'{item["addressLine1"]}, {item["addressLine2"]}, {item["city"]}, {item["postCode"]}'
        if item['location'].replace(',','').strip() == '':
            item['location'] = ''
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    }) 

# =================================================== Location ======================================================
@api_view(['GET'])
def searchLocation(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    locations = Location.objects.filter(organization=request.user.organization)
    recordsTotal = locations.count()

    locations = locations.filter(Q(addressLine1__contains=keyword) | Q(addressLine2__contains=keyword) | Q(postCode__contains=keyword))
    locations = locations.order_by('-createdDate')
    
    recordsFiltered = locations.count()
    locations = locations[start:start+length]
    data = LocationSerializer(locations, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })     

@api_view(['POST'])
def deleteLocation(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            location = Location.objects.get(pk=pk)
            location.delete()
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': 'Wrong password'})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

