from django.db.models import Q
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.timezone import make_aware

import json
import requests
import traceback
from time import time
from datetime import datetime, timedelta

from. param_utils import getTenantParamValue, getSystemParamValue
from .models import *
from .serializers import *
from .log_utils import logAction


# ================================================ LogIn ========================================================

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
        startDate = make_aware(datetime.strptime(startDate, '%d/%m/%Y'))
        logIns = logIns.filter(date__gte=startDate)

    if endDate:
        endDate = make_aware(datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1))
        logIns = logIns.filter(date__lt=endDate)                        

    logIns = logIns.order_by('-date')
    recordsFiltered = logIns.count()
    logIns = logIns[start:start+length]
    data = LogInSerializer(logIns, many=True).data

    for item in data:
        item['user'] = f'{item["userFullName"]}'
        diff = timezone.now() - item['date']
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

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getLastCheckInTime(request):
    lastCheckIn = CheckIn.objects.filter(organization=request.user.organization, status=CheckIn.Status.SUCCESS).order_by('-date').first()
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
    newCheckIn = None

    if lastUpdated != '':
        lastUpdatedTime = make_aware(datetime.strptime(lastUpdated, '%d/%m/%Y %H:%M:%S'))
        lastCheckIn = CheckIn.objects.filter(organization=request.user.organization, status=CheckIn.Status.SUCCESS).order_by('-date').first()

        if lastCheckIn:
            newCheckIn = CheckInSerializer(lastCheckIn).data
            lastCheckInDate = lastCheckIn.date
            updated = int(datetime.timestamp(lastCheckInDate)) > int(datetime.timestamp(lastUpdatedTime))

            newCheckIn['user'] = newCheckIn["userFullName"]
            newCheckIn['geoLocation'] = {'lat': newCheckIn['lat'], 'lng': newCheckIn['lng']}
                
    return Response({'updated': updated, 'lastUpdated': newCheckIn['date'],
                         'newCheckIn': newCheckIn})

def parseHourMin(flushTime):
    hour, minute = None, None

    arr = flushTime.split(':')

    if len(arr) == 2 and arr[0].isdigit() and arr[1].isdigit():
        hour = int(arr[0])
        minute = int(arr[1])
        if not (0 <= hour <= 23): hour = None
        if not (0 <= minute <= 59): minute = None        

    return hour, minute
        
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchCheckIn(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')    
    userId = request.query_params.get("userId")
    locationId = request.query_params.get("locationId")
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")
    
    mapView = request.query_params.get("mapView")
    if mapView:
        flushTime = getTenantParamValue('MAP_VIEW_FLUSH_TIME', request.user.organization, settings.MAP_VIEW_FLUSH_TIME)
        hour, minute = parseHourMin(flushTime)
        
        if hour and minute:
            now = timezone.now()
            flushTime = timezone.now().replace(hour=hour, minute=minute, second=0, microsecond=0) 
            if flushTime >= now:
                flushTime -= timedelta(days=1)

            startDate = flushTime
            endDate = None
        else:
            startDate = endDate = None
    else:
        startDate = make_aware(datetime.strptime(startDate, '%d/%m/%Y')) if startDate else None
        endDate = make_aware(datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1)) if endDate else None
        
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

    for i,item in enumerate(data):
        item['user'] = f'{item["userFullName"]}'
        item['statusText'] = CheckIn.Status.messages.get(item['status'])
        
        tmp = f'{item["addressLine1"]}, {item["addressLine2"]}, {item["city"]}, {item["postCode"]}'
        if tmp.replace(',', '').strip() == '':
            tmp = ''

        item['location'] = tmp
        
        diff = timezone.now() - checkIns[i].date
        seconds = diff.seconds + diff.days * 24 * 3600
        
        minutes = seconds // 60
        hours = seconds // 3600
        
        if hours == 0:
            item['datediff'] = f'{minutes} minute{"" if minutes == 1 else "s"}'
        else:
            item['datediff'] = f'{hours} hour{"" if hours == 1 else "s"}'

        if item['lat'] and item['lng']:
            item['geoLocation'] = {'lat': item['lat'], 'lng': item['lng']}

    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

# =================================================== Role ==============================================================
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getAdminRoleId(request):
    adminRole = Role.objects.filter(code='ADMIN').first()
    adminRoleId = adminRole.id if adminRole else -1
    return Response({'adminRoleId' : adminRoleId})

# =================================================== Organization ======================================================

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
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
        tenantAdmin = User.objects.filter(username=org.adminUsername).first()
        data[i]['admin'] = {'name': tenantAdmin.fullname if tenantAdmin else "", 'email': tenantAdmin.email if tenantAdmin else ""}
        data[i]['userCount'] = User.objects.filter(organization=org).count()
        data[i]['deviceCount'] = Device.objects.filter(organization=org).count()
        data[i]['status'] = tenantAdmin.status if tenantAdmin else User.Status.INVITED
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def deleteOrganization(request, pk):    
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            organization = Organization.objects.get(pk=pk)  
            logAction('DELETE', request.user, organization, None)
            organization.delete()  
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

# =================================================== User ======================================================
def isValidLng(lng):
    try:
        lng = float(lng)
        return -180 <= lng <= 180
    except:
        return False

def isValidLat(lat):
    try:
        lat = float(lat)
        return -90 <= lat <= 90
    except:
        return False

def getUserData(user):
    nfcEnabled = qrScanEnabled = sharedLocation = False

    if user.organization:
        nfcEnabled = user.nfcEnabled and user.organization.nfcEnabled
        qrScanEnabled = user.qrScanEnabled and user.organization.qrScanEnabled
        sharedLocation = user.sharedLocation

    data = {
        'fullname': user.fullname, 
        'email': user.email,
        'nfcEnabled': nfcEnabled,
        'qrScanEnabled': qrScanEnabled,
        'sharedLocation': sharedLocation,
        'roles': user.role_codes
    }

    if user.profilePicture:
        data['profilepicture'] = settings.HOST_URL + '/' +  user.profilePicture.url

    if user.organization:
        data['company'] = user.organization.name
        data['NFCButtonText'] = getTenantParamValue('NFC_BUTTON_TEXT', user.organization, settings.NFC_BUTTON_TEXT)
        data['QRButtonText'] = getTenantParamValue('QR_BUTTON_TEXT', user.organization, settings.QR_BUTTON_TEXT)

    if user.hasAnyRole(['ADMIN', 'INSTALLER']):
        data['UpdateDeviceCoordinatesButtonText'] = getTenantParamValue('UPDATE_DEVICE_COORDINATES_BUTTON_TEXT', user.organization, settings.UPDATE_DEVICE_COORDINATES_BUTTON_TEXT) 

    if user.is_superuser:
        data['SetDeviceUIDButtonText'] = getSystemParamValue('SET_DEVICE_UID_BUTTON_TEXT', settings.SET_DEVICE_UID_BUTTON_TEXT)        
    
    return data

@api_view(['POST'])
def logIn(request):
    mobiletime = float(request.data.get('mobiletime', '0'))
    
    headers = {'Content-type': 'application/json'}
    resp_text = requests.post(settings.HOST_URL + "/api/token", data=json.dumps(request.data), headers=headers).text    
    resp = json.loads(resp_text)
    user = User.objects.filter(username=request.data.get("username")).first()

    if not user or not resp.get('access'):
        return Response({
            "success": False,
            "message": _('incorrect.username.or.password')
        })

    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW', settings.MAX_TIME_DIFF_ALLOW)
    
    if abs(mobiletime - time()) > allowedTimeDiff:
        return Response({
            "success": False,
            "message": _("incorrect.mobile.time")
        })

    logIn = LogIn()
    logIn.user = user
    logIn.date = timezone.now()
    logIn.fromMobileApp = True
    logIn.save()
    
    data = getUserData(user)
    data['success'] = True
    data['access'] = resp['access']
     
    return Response(data)

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getUserInfo(request):    
    data = getUserData(request.user)
    data['success'] = True
    return Response(data)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def userCheckIn(request):
    if not request.user.organization or not request.user.hasAnyRole(['ADMIN', 'STAFF', 'USER']):
        return Response({'success': False, 'message': _('no.permission')})

    code = request.data.get("scanCode", "")
    position = request.data.get("position", {})
    lat = position.get("lat")
    lng = position.get("lng")
    
    uid = request.data.get("uid", "")
    scantime = float(request.data.get("scantime", 0))
    
    checkIn = CheckIn()
    checkIn.user = request.user
    checkIn.organization = request.user.organization
    checkIn.scanCode = code
    checkIn.uid = uid
    checkIn.lat = lat
    checkIn.lng = lng
    checkIn.date = datetime.fromtimestamp(scantime)

    message_params = []
    status = CheckIn.Status.SUCCESS

    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW', settings.MAX_TIME_DIFF_ALLOW)

    if abs(scantime - time()) > allowedTimeDiff:
        status = CheckIn.Status.INCORRECT_MOBILE_TIME

    if status == CheckIn.Status.SUCCESS and (not isValidLat(lat) or not isValidLng(lng)):
        status = CheckIn.Status.INVALID_GPS_POSITION
    
    device = None

    if status == CheckIn.Status.SUCCESS :
        arr = code.split('-')
        if len(arr) != 3 or arr[0] != settings.SCAN_CODE_PREFIX:
            status = CheckIn.Status.INVALID_DEVICE_CODE
        else:
            id1, id2 = arr[1:]
            device = Device.objects.filter(id1=id1, id2=id2, organization=request.user.organization).first()
            checkIn.device = device
            checkIn.location = device.installationLocation if device else None
    
    if status == CheckIn.Status.SUCCESS and not device:
        status = CheckIn.Status.DEVICE_NOT_REGISTERED
        
    if status == CheckIn.Status.SUCCESS and device.uid != uid:
        status = CheckIn.Status.INCORRECT_DEVICE_UID

    lastCheckIn = CheckIn.objects.filter(user=request.user,status=CheckIn.Status.SUCCESS).order_by('-date').first()
    scanDelay = getTenantParamValue('SCAN_TIME_DELAY', request.user.organization, settings.SCAN_TIME_DELAY)

    if lastCheckIn and scanDelay > 0:
        if scanDelay == int(scanDelay):
            scanDelay = int(scanDelay)

        timediff = scantime - datetime.timestamp(lastCheckIn.date)

        if status == CheckIn.Status.SUCCESS and timediff < scanDelay * 60:
            status = CheckIn.Status.SCAN_NOT_TIME_OUT_YET
            message_params = [scanDelay]

    checkIn.status = status        
    checkIn.save()
    logAction('CREATE', request.user, None, checkIn)

    if status == CheckIn.Status.SUCCESS:
        location = str(device.installationLocation)
        message_params = [location]

    return Response({
        'success': status == CheckIn.Status.SUCCESS, 
        'message': CheckIn.Status.mobile_messages.get(status, '') % tuple(message_params)
    })

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getUserCheckInHistory(request):
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")
    
    startDate = datetime.strptime(startDate, '%d/%m/%Y') if startDate else None
    endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1) if endDate else None

    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 10))
    
    checkIns = CheckIn.objects.filter(user__id=request.user.id, status=CheckIn.Status.SUCCESS)

    if startDate:        
        checkIns = checkIns.filter(date__gte=startDate)

    if endDate:        
        checkIns = checkIns.filter(date__lt=endDate)
        
    checkIns = checkIns.order_by('-date')
    checkIns = checkIns[start:start+length]
    
    result = []

    for item in checkIns:
        result.append({
            'location': str(item.location),
            'date': item.date.strftime('%d/%m/%Y %H:%M:%S') if item.date else '',
            'position': {
                'lat': item.lat,
                'lng': item.lng
            }
        })

    return Response({
        "data": result
    })

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def changeUserPassword(request):
    user = request.user
    oldPassword = request.data.get('oldPassword', '')
    newPassword = request.data.get('newPassword', '')

    mobiletime = float(request.data.get('mobiletime', '0'))
    
    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW',  settings.MAX_TIME_DIFF_ALLOW)
    
    if abs(mobiletime - time()) > allowedTimeDiff:
        return Response({
            "success": False,
            "message": _("incorrect.mobile.time")
        })
        
    if not user.check_password(oldPassword):
        return Response({
            'success': False,
            'message': _('incorrect.old.password')
        })

    if newPassword == '':
        return Response({
            'success': False,
            'message': _('new.password.empty')
        })

    if len(newPassword) < 8:
        return Response({
            'success': False,
            'message': _('new.password.too.short')
        })

    if newPassword.isdigit():
        return Response({
            'success': False,
            'message': _('new.password.cannot.be.all.digits')
        })
    
    user.password = make_password(newPassword)
    user.save()

    return Response({'success': True})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchUser(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))

    if request.query_params.get("organizationId"):
        organization = Organization.objects.get(pk=request.query_params.get("organizationId"))
    else:
        organization=request.user.organization
    
    users = User.objects.filter(organization=organization)
    recordsTotal = users.count()

    users = users.filter(Q(fullname__contains=keyword) | Q(email__contains=keyword))
    users = users.order_by('-createdDate')
    
    recordsFiltered = users.count()
    users = users[start:start+length]
    data = UserSerializer(users, many=True).data
    tenantAdminName = organization.adminUsername if organization else None

    for i, user in enumerate(users):
        locked = user.hasRole('ADMIN')

        if request.user.username == tenantAdminName  and user.username != tenantAdminName:
            locked = False

        data[i]['locked'] = locked
        data[i]['role_names'] = user.role_names
        
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data,
    })

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def viewUserDetails(request, pk):    
    user = User.objects.get(pk=pk)
    data = UserSerializer(user).data
    data['role_names'] = user.role_names
    return Response(data)

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def deleteUser(request, pk):   
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            user = User.objects.get(pk=pk)    
            logAction('DELETE', request.user, user, None)
            user.delete() 
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

# =================================================== Device ======================================================
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def addDevice(request):
    if not request.user.is_superuser:
        return Response({'success': False, 'message': _('no.permission')})

    mobiletime = float(request.data.get('mobiletime', '0'))
    
    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW',  settings.MAX_TIME_DIFF_ALLOW)
    
    if abs(mobiletime - time()) > allowedTimeDiff:
        return Response({
            "success": False,
            "message": _("incorrect.mobile.time")
        })

    uid = request.data.get('uid', '')
    code = request.data.get('scanCode', '')

    if uid == '':
        return Response({
            "success": False,
            "message": _("invalid.uid.value")
        })

    if Device.objects.filter(uid=uid).count() > 0:
        return Response({
            "success": False,
            "message": f'{_("device.with")} {_("uid")}={uid} {_("already.exists")}'
        })

    arr = code.split('-')
    if len(arr) != 3 or arr[0] != settings.SCAN_CODE_PREFIX or arr[1] == '' or arr[2] == '':
        return Response({
            "success": False,
            "message": _("invalid.scan.code")
        })        
    
    id1, id2 = arr[1:]
    if Device.objects.filter(id1=id1, id2=id2).count() > 0:    
        return Response({
            "success": False,
            "message": f'{_("device.with")} {_("id1")}={id1} & {_("id2")}={id2} {_("already.exists")}'
        })
    
    device = Device()
    device.uid = uid
    device.id1 = id1
    device.id2 = id2
    device.save()
    logAction('CREATE', request.user, None, device)

    return Response({"success": True})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def updateDeviceCoordinates(request):
    if not request.user.organization or not request.user.hasAnyRole(['ADMIN', 'INSTALLER']):
        return Response({'success': False, 'message': _('no.permission')})

    mobiletime = float(request.data.get('mobiletime', '0'))
    
    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW', settings.MAX_TIME_DIFF_ALLOW)
    
    if abs(mobiletime - time()) > allowedTimeDiff:
        return Response({
            "success": False,
            "message": _("incorrect.mobile.time")
        })

    uid = request.data.get("uid", "")
    position = request.data.get("position", {})
    lat = position.get("lat")
    lng = position.get("lng")

    if not isValidLat(lat) or not isValidLng(lng):
        return Response({
            "success": False,
            "message": _("invalid.position")
        })

    old_device = Device.objects.filter(organization=request.user.organization, uid=uid).first()
    device = Device.objects.filter(organization=request.user.organization, uid=uid).first()
    
    if not device:
        return Response({
            "success": False,
            "message": _("no.device.with.provided.uid")
        })

    device.lat = lat
    device.lng = lng
    logAction('UPDATE', request.user, old_device, device)
    device.save()

    return Response({"success": True}) 


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getAllNFCTags(request):
    if not request.user.organization:
        return Response({'success': False, 'message': _('no.permission')})

    devices = Device.objects.filter(organization=request.user.organization,
                 uid__isnull=False, lat__isnull=False, lng__isnull=False)
    result = []

    for device in devices:
        result.append({
            'uid': device.uid,
            'position': {
                'lat': device.lat,
                'lng': device.lng
            }
        })

    return Response(result)

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
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
@permission_classes((IsAuthenticated,))
def deleteDevice(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            device = Device.objects.get(pk=pk)    
            logAction('DELETE', request.user, device, None)
            device.delete()  
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def deleteDeviceFromOrg(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            old_device = Device.objects.get(pk=pk)
            device = Device.objects.get(pk=pk)
            device.organization = None
            device.installationLocation = None            
            device.save()
            logAction('RELEASE', request.user, old_device, device)
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
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
@permission_classes((IsAuthenticated,))
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
@permission_classes((IsAuthenticated,))
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
@permission_classes((IsAuthenticated,))
def deleteLocation(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            location = Location.objects.get(pk=pk)
            logAction('DELETE', request.user, location, None)
            location.delete()
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchLocationByPostCode(request):
    q = request.GET.get('q')
    if q:
        resp_text = requests.get(settings.POST_CODER_API_URL + q + '?format=json&lines=2').text
        try:
            items = json.loads(resp_text)

            items = [{
                        'addressLine1': item.get('addressline1', ''),
                        'addressLine2': item.get('addressline2', ''),
                        'city': item.get('city', ''),
                        'postCode': item.get('postcode', ''),
                        
                    } for i,item in enumerate(items)]

            return Response({'items': items, 'success': True})
        except:           
            return Response({'error': resp_text, 'success': False})
    else:
        return Response({'items': [], 'success': True})

# =================================================== Mail Templates ======================================================
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getMailTemplateContent(request, pk):
    template = MailTemplate.objects.filter(pk=pk).first()
    if template:
        return Response({'success': True, 'subject': template.subject, 'body': template.body})

    return Response({'success': False})