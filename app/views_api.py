from django.db.models import Q
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.timezone import make_aware

import math
import json
import requests
import traceback
from time import time
from datetime import datetime, timedelta

from. param_utils import getTenantParamValue, getSystemParamValue
from .models import *
from .serializers import *
from .log_utils import logAction
from .img_utils import resizeProfileImage

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
    
    if userId:
        logIns = logIns.filter(user__id=int(userId))

    if startDate:
        startDate = make_aware(datetime.strptime(startDate, '%d/%m/%Y'))
        logIns = logIns.filter(date__gte=startDate)

    if endDate:
        endDate = make_aware(datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1))
        logIns = logIns.filter(date__lt=endDate)                        

    recordsTotal = logIns.count()

    if keyword != '':
        logIns = logIns.filter(user__fullname__contains=keyword)

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
    newCheckIn = {}

    if lastUpdated != '':
        users = request.user.viewed_users
        lastUpdatedTime = make_aware(datetime.strptime(lastUpdated, '%d/%m/%Y %H:%M:%S'))
        lastCheckIn = CheckIn.objects.filter(user__in=users, status=CheckIn.Status.SUCCESS).order_by('-date').first()

        if lastCheckIn:
            newCheckIn = CheckInSerializer(lastCheckIn).data
            lastCheckInDate = lastCheckIn.date
            updated = int(datetime.timestamp(lastCheckInDate)) > int(datetime.timestamp(lastUpdatedTime))

            newCheckIn['user'] = newCheckIn["userFullName"]
            newCheckIn['geoLocation'] = {'lat': newCheckIn['lat'], 'lng': newCheckIn['lng']}
                
    return Response({'updated': updated, 'lastUpdated': newCheckIn.get('date'),
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
    status = request.query_params.get("status")
    locationId = request.query_params.get("locationId")
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")
    
    mapView = request.query_params.get("mapView")
    if mapView:
        flushTime = getTenantParamValue('MAP_VIEW_FLUSH_TIME', request.user.organization, settings.MAP_VIEW_FLUSH_TIME)
        
        hour, minute = parseHourMin(flushTime)
        
        if hour != None and minute != None:
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
    
    checkIns = CheckIn.objects.all()
    
    if userId:
        checkIns = checkIns.filter(user__id=int(userId))
    else:
        checkIns = checkIns.filter(user__in=request.user.viewed_users)

    if status == '1':
        checkIns = checkIns.filter(status=CheckIn.Status.SUCCESS)
    elif status == '2':
        checkIns = checkIns.filter(~Q(status=CheckIn.Status.SUCCESS)) 

    if locationId:
        checkIns = checkIns.filter(location__id=int(locationId))

    if startDate:        
        checkIns = checkIns.filter(date__gte=startDate)

    if endDate:        
        checkIns = checkIns.filter(date__lt=endDate)
        
    recordsTotal = checkIns.count()

    if keyword != '':
        checkIns = checkIns.filter(Q(user__fullname__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword)
                                | Q(location__city__contains=keyword)
                                | Q(location__postCode__contains=keyword))

    checkIns = checkIns.order_by('-date')
    recordsFiltered = checkIns.count()
    checkIns = checkIns[start:start+length]
    data = CheckInSerializer(checkIns, many=True).data

    for i,item in enumerate(data):
        item['user'] = f'{item["userFullName"]}'
        item['statusText'] = CheckIn.Status.messages.get(item['status'])
        
        tmp = f'{item["addressLine1"]}, {item["addressLine2"] or ""}, {item["city"]}, {item["postCode"]}'
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

# =================================================== Organization ======================================================

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchOrganization(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    organizations = Organization.objects.all()

    if not request.user.is_superuser:
        organizations = organizations.filter(createdBy=request.user)

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
    scanDelay = 0
 
    if user.organization:
        scanDelay = getTenantParamValue('SCAN_TIME_DELAY', user.organization, settings.SCAN_TIME_DELAY)      

    data = {
        'fullname': user.fullname, 
        'email': user.email,
        'nfcEnabled': True,
        'sharedLocation': True,
        'roles': 'ADMIN' if user.is_tenant_admin else 'USER',
        'scanDelay': scanDelay,
        'iosAppVersion': getSystemParamValue('IOS_APP_VERSION', '1.0'),
        'isIOSNewUpdate': getSystemParamValue('IS_IOS_APP_NEW_UPDATE') == 1,
        'androidAppVersion': getSystemParamValue('ANDROID_APP_VERSION', '1.0'),
        'isAndroidNewUpdate': getSystemParamValue('IS_ANDROID_APP_NEW_UPDATE') == 1
    }

    if user.profilePicture:
        data['profilepicture'] = settings.HOST_URL + '/' +  user.profilePicture.url

    if user.organization:
        data['company'] = user.organization.name
        data['NFCButtonText'] = getTenantParamValue('NFC_BUTTON_TEXT', user.organization, settings.NFC_BUTTON_TEXT)
        data['QRButtonText'] = ''
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

def removeDoorNumbert(s):
    s = s.replace('Unnamed Road,', '').strip()
    pos = s.find(' ')
    if pos > 0 and s[:pos].isdigit():
        return s[pos:].strip()
    return s

def getAdressFromGeoLocation(lat, lng):
    url = settings.GMAP_ADDRESS_API_URL + f'&latlng={lat},{lng}'
    try:
        resp = requests.get(url)
        obj = json.loads(resp.text)
        return removeDoorNumbert(obj['results'][0]['formatted_address'])
    except:
        return ''

def checkDistance(lat1, lng1, lat2, lng2, maxCheckInDistance):
    if lat1 == None or lng1 == None or lat2 == None or lng2 == None:
        return False

    R = 6371
    lat = (lat1+lat2)/2
    phi = math.pi * lat/180
    R1 = R * math.cos(phi)
    dx = R1 * math.pi * abs(lng2-lng1)/180
    dy = R * math.pi * abs(lat2-lat1)/180
    return 1000*math.sqrt(dx*dx + dy*dy) <= maxCheckInDistance 

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def userCheckIn(request):
    if not request.user.organization:
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
    checkIn.address = getAdressFromGeoLocation(lat, lng)
    checkIn.date = datetime.fromtimestamp(scantime)

    message_params = []
    status = CheckIn.Status.SUCCESS

    maxCheckInDistance = getSystemParamValue('MAX_CHECK_IN_DISTANCE', settings.MAX_CHECK_IN_DISTANCE)
    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW', settings.MAX_TIME_DIFF_ALLOW)

    if abs(scantime - time()) > allowedTimeDiff:
        status = CheckIn.Status.INCORRECT_MOBILE_TIME

    if status == CheckIn.Status.SUCCESS and (not isValidLat(lat) or not isValidLng(lng)):
        status = CheckIn.Status.INVALID_GPS_POSITION

    device = None

    arr = code.split('-')
    if len(arr) != 3 or arr[0] != settings.SCAN_CODE_PREFIX:
        if status == CheckIn.Status.SUCCESS:
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

    if status == CheckIn.Status.SUCCESS and not device.enabled:
        status = CheckIn.Status.DEVICE_DISABLED

    lastCheckIn = CheckIn.objects.filter(user=request.user,status=CheckIn.Status.SUCCESS).order_by('-date').first()
    scanDelay = getTenantParamValue('SCAN_TIME_DELAY', request.user.organization, settings.SCAN_TIME_DELAY)

    if lastCheckIn and scanDelay > 0:
        if scanDelay == int(scanDelay):
            scanDelay = int(scanDelay)

        timediff = scantime - datetime.timestamp(lastCheckIn.date)

        if status == CheckIn.Status.SUCCESS and timediff < scanDelay:
            status = CheckIn.Status.SCAN_NOT_TIME_OUT_YET
            message_params = [scanDelay]

    if status == CheckIn.Status.SUCCESS and not checkDistance(lat, lng, device.lat, device.lng, maxCheckInDistance):
        status = CheckIn.Status.MAX_DISTANCE_EXCEED

    checkIn.status = status        
    checkIn.save()
    logAction('CHECK_IN', request.user, None, checkIn)

    if status == CheckIn.Status.SUCCESS:
        location = str(device.installationLocation)
        message_params = [location]

    return Response({
        'success': status == CheckIn.Status.SUCCESS, 
        'statusCode': 1 if status == CheckIn.Status.SUCCESS else (2 if status != CheckIn.Status.SCAN_NOT_TIME_OUT_YET else 3),        
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
            'date': timezone.localtime(item.date).strftime('%d/%m/%Y %H:%M:%S') if item.date else '',
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
def updateUserProfile(request):
    
    mobiletime = float(request.data.get('mobiletime', '0'))
    allowedTimeDiff = getSystemParamValue('MAX_TIME_DIFF_ALLOW',  settings.MAX_TIME_DIFF_ALLOW)

    fullname = request.data.get('fullname', '')
    profilePicture = request.data.get('profilePicture')

    if abs(mobiletime - time()) > allowedTimeDiff:
        return Response({
            "success": False,
            "message": _("incorrect.mobile.time")
        })

    if fullname.strip() == '':
        return Response({
            "success": False,
            "message": _("fullname.cannot.be.blank")
        })
    
    user = request.user
    user.fullname = fullname
    if profilePicture and profilePicture.name != '' :
        user.profilePicture = resizeProfileImage(profilePicture)
    user.save()
    return Response({'success': True})

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
def getUsersByOrganization(request):
    organizationId = request.query_params.get('organizationId')
    users = User.objects.filter(organization__id=organizationId)
    data = [{'id': user.id, 'fullname': user.fullname} for user in users]
    return Response({'users': data})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchUser(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    isReseller = request.query_params.get('isReseller')

    if request.query_params.get("organizationId"):
        organization = Organization.objects.get(pk=request.query_params.get("organizationId"))
    else:
        organization=request.user.organization
    
    if isReseller:
        users = User.objects.filter(isReseller=True)
    else:
        users = User.objects.filter(organization=organization)

    recordsTotal = users.count()

    users = users.filter(Q(fullname__contains=keyword) | Q(email__contains=keyword))
    users = users.order_by('-createdDate')
    
    recordsFiltered = users.count()
    users = users[start:start+length]
    data = UserSerializer(users, many=True).data
    tenantAdminName = organization.adminUsername if organization else None

    for i, user in enumerate(users):
        locked = user.is_tenant_admin

        if request.user.username == tenantAdminName  and user.username != tenantAdminName:
            locked = False

        if user.id == request.user.id:
            locked = True

        data[i]['is_admin'] = user.is_tenant_admin
        data[i]['locked'] = locked
        data[i]['group_names'] = user.group_names

        if data[i]['profilePicture'] and not data[i]['profilePicture'].startswith('/'):
            data[i]['profilePicture'] = '/' + data[i]['profilePicture']
        
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
    data['group_names'] = user.group_names
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

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def disableUser(request, pk):
    try:
        old_user = User.objects.get(pk=pk)  
        user = User.objects.get(pk=pk)  

        if request.user.is_superuser:
            user.status = User.Status.LOCK_BY_SUPER_ADMIN
            user.is_active = False

        elif request.user.hasPagePermission('USERS', 'EDIT'):
            user.status = User.Status.LOCK_BY_TENANT_ADMIN
            user.is_active = False

        else:
            return Response({'success': False, 'error': _('no.permission')})
            
        user.save()
        logAction('UPDATE', request.user, old_user, user)

        return Response({'success': True})

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def enableUser(request, pk):
    try:
        old_user = User.objects.get(pk=pk) 
        user = User.objects.get(pk=pk)  

        if request.user.is_superuser:
            user.status = User.Status.ACTIVE
            user.is_active = True

        elif request.user.hasPagePermission('USERS', 'EDIT'):
            if user.status == User.Status.LOCK_BY_SUPER_ADMIN:
                return Response({'success': False, 'error': _('user.locked.by.super.admin')})
            else:
                user.status = User.Status.ACTIVE
                user.is_active = True

        else:
            return Response({'success': False, 'error': _('no.permission')})
            
        user.save()
        logAction('UPDATE', request.user, old_user, user)
        
        return Response({'success': True})

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
    device.createdDate = timezone.now()
    device.enabled = True
    device.status = Device.Status.ENABLED  
    device.save()
    logAction('CREATE', request.user, None, device)

    return Response({"success": True})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def updateDeviceCoordinates(request):
    if not request.user.organization:
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

    if not device.enabled:
        return Response({
            "success": False,
            "message": _("device.has.been.disabled")
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
    if not request.user.is_superuser and not request.user.isReseller:
        return Response({'success': False, 'message': _('no.permission')})
        
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    devices = Device.objects.filter(organization__isnull=True)

    if not request.user.is_superuser:
        devices = devices.filter(createdBy=request.user)

    recordsTotal = devices.count()

    devices = devices.filter(Q(id1__contains=keyword) 
                            | Q(id2__contains=keyword) 
                            | Q(uid__contains=keyword)).order_by('-createdDate')

    recordsFiltered = devices.count()
    devices = devices[start:start+length]
    data = UnRegisteredDeviceSerializer(devices, many=True).data
    
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

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def disableDevice(request, pk):
    try:
        old_device = Device.objects.get(pk=pk)  
        device = Device.objects.get(pk=pk)  

        if request.user.is_superuser:
            device.status = Device.Status.LOCK_BY_SUPER_ADMIN
            device.enabled = False

        elif request.user.hasPagePermission('DEVICES', 'EDIT'):
            device.status = Device.Status.LOCK_BY_TENANT_ADMIN
            device.enabled = False

        else:
            return Response({'success': False, 'error': _('no.permission')})
            
        device.save()
        logAction('UPDATE', request.user, old_device, device)

        return Response({'success': True})

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def enableDevice(request, pk):
    try:
        old_device = Device.objects.get(pk=pk) 
        device = Device.objects.get(pk=pk)  

        if request.user.is_superuser:
            device.status = Device.Status.ENABLED
            device.enabled = True

        elif request.user.hasPagePermission('DEVICES', 'EDIT'):
            if device.status == Device.Status.LOCK_BY_SUPER_ADMIN:
                return Response({'success': False, 'error': _('device.locked.by.super.admin')})
            else:
                device.status = Device.Status.ENABLED
                device.enabled = True

        else:
            return Response({'success': False, 'error': _('no.permission')})
            
        device.save()
        logAction('UPDATE', request.user, old_device, device)
        
        return Response({'success': True})

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
            logAction('UPDATE', request.user, old_device, device)
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
    
    if not request.user.is_superuser:
        devices = devices.filter(createdBy=request.user)

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
        item['location'] = f'{item["addressLine1"]}, {item["addressLine2"] or ""}, {item["city"]}, {item["postCode"]}'
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

# =================================================== Groups ======================================================
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchGroup(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    groups = Group.objects.filter(organization=request.user.organization)
    recordsTotal = groups.count()

    groups = groups.filter(name__contains=keyword)
    
    recordsFiltered = groups.count()
    groups = groups[start:start+length]
    data = GroupSerializer(groups, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })     

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def deleteGroup(request, pk):
    try:
        password = request.data.get('password', '')

        if request.user.check_password(password):
            group = Group.objects.get(pk=pk)
            logAction('DELETE', request.user, group, None)
            group.delete()
            return Response({'success': True})    
        else:
            return Response({'success': False, 'error': _('wrong.password')})    

    except Exception as e:
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)})

# =================================================== Mail Templates ======================================================
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getMailTemplateContent(request, pk):
    template = MailTemplate.objects.filter(pk=pk).first()
    if template:
        return Response({'success': True, 'subject': template.subject, 'body': template.body})

    return Response({'success': False})

# =================================================== Log ======================================================
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def markAllLogsAsRead(request):
    logs = []

    if request.user.is_superuser:
        logs = Log.objects.filter(~Q(viewUsers=request.user))

    elif request.user.is_tenant_admin:
        logs = Log.objects.filter(organization=request.user.organization).filter(~Q(viewUsers=request.user))

    for log in logs:
        log.viewUsers.add(request.user)
        log.save()

    return Response({'success': True})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def checkForNewLogs(request):
    currentCount = int(request.query_params.get('currentCount', 0))
    log_count = request.user.count_new_logs
    if log_count > currentCount:
        logs = request.user.get_new_logs
        logs = [{'id': log.id, 'content': str(log)} for log in logs]
        return Response({'logs': logs, 'log_count': log_count, 'updated': True})
    else:
        return Response({'updated': False, 'log_count': 0})

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def searchLog(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '') 
    
    fromSuperAdmin = request.query_params.get('fromSuperAdmin')
    viewStatus = request.query_params.get('viewStatus')
    organizationId = request.query_params.get('organizationId')
    userId = request.query_params.get("userId")
    actionId = request.query_params.get("actionId")

    modelName = request.query_params.get("modelName")
    startDate = request.query_params.get("startDate")
    endDate = request.query_params.get("endDate")

    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    logs = Log.objects.all()

    if not fromSuperAdmin:
        if userId:
            logs = logs.filter(performUser__id=userId)
        else:        
            logs = logs.filter(performUser__in=request.user.viewed_users)
    else:
        if organizationId:
            logs = logs.filter(organization=organizationId)
        elif not request.user.is_superuser:
            organizations = Organization.objects.filter(createdBy=request.user)
            logs = logs.filter(organization__in=organizations)

        if userId:
            logs = logs.filter(performUser__id=userId)
        
    if viewStatus == '1':
        logs = logs.filter(~Q(viewUsers=request.user))
    elif viewStatus == '2':
        logs = logs.filter(viewUsers=request.user)
            
    if actionId:
        logs = logs.filter(action__id=actionId)

    if modelName:
        logs = logs.filter(modelName=modelName)

    if startDate:
        startDate = datetime.strptime(startDate, '%d/%m/%Y')
        logs = logs.filter(actionDate__gte=startDate)

    if endDate:
        endDate = datetime.strptime(endDate, '%d/%m/%Y') + timedelta(days=1)
        logs = logs.filter(actionDate__lt=endDate) 

    recordsTotal = logs.count()

    if keyword != '':
        logs = logs.filter(Q(performUser__fullname__contains=keyword) 
                    | Q(modelName__contains=keyword) 
                    | Q(action__name__contains=keyword))

    recordsFiltered  = logs.count()

    logs = logs.order_by('-actionDate')
    
    logs = logs[start:start+length]

    data = LogSerializer(logs, many=True).data
    for i,item in enumerate(data):
        item['unviewed'] = request.user not in logs[i].viewUsers.all()

    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })