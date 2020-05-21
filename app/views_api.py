from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from datetime import datetime

from .models import *
from .serializers import *

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def test(request):
    return Response({'success': True})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def checkIn(request):
    code = request.data.get("code")
    print('Code=', code)
    arr = code.split('-')
    if len(arr) != 3 or arr[0] != "SCANX":
        return Response({'error': 'Wrong code'})
    
    id1, id2 = arr[1:]
    device = Device.objects.filter(id1=id1).filter(id2=id2).first()
    if not device:
        return Response({'error': 'No device found'})

    print(device.id1, device.id2, device.installationLocation)

    checkIn = CheckIn()
    checkIn.location = device.installationLocation
    checkIn.device = device
    checkIn.user = request.user
    checkIn.date = datetime.now()
    checkIn.save()

    return Response({'device': f'{device.id1}-{device.id2}', 'location': str(device.installationLocation)})

@api_view(['GET'])
def searchCheckIn(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    checkIns = CheckIn.objects.filter(user__organization=request.user.organization)
    recordsTotal = checkIns.count()

    checkIns = checkIns.filter(Q(user__fullname__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword) 
                                | Q(location__addressLine1__contains=keyword)) \
                        .order_by('-date')

    recordsFiltered = checkIns.count()
    checkIns = checkIns[start:start+length]
    data = CheckInSerializer(checkIns, many=True).data

    for item in data:
        item['location'] = f'{item["addressLine1"]}, {item["addressLine2"]}'
        d = datetime.strptime(item['date'], "%d %b %Y at %I:%M %p")
        minutes = (datetime.now() - d).seconds // 60
        hours = (datetime.now() - d).seconds // 3600
        
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
        staff = User.objects.filter(organization=org).filter(is_staff=True).first()
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
def deleteOrganization(request, pk):    
    try:
        organization = Organization.objects.get(pk=pk)    
        organization.delete()
        return Response({'success': True})    
    except:
        return Response({'success': False, 'message': 'Cannot delete this organization because some records depend on it'})

# =================================================== User ======================================================

@api_view(['GET'])
def searchUser(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    users = User.objects.filter(organization=request.user.organization)
    recordsTotal = users.count()

    users = users.filter(Q(fullname__contains=keyword) | Q(email__contains=keyword)).order_by('-createdDate')
    recordsFiltered = users.count()
    users = users[start:start+length]
    data = UserSerializer(users, many=True).data

    staff = [item for item in data if item['is_staff']]
    non_staff = [item for item in data if not item['is_staff']]

    data = staff + non_staff
        
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })

@api_view(['GET'])
def deleteUser(request, pk):    
    try:
        user = User.objects.get(pk=pk)    
        user.delete()
        return Response({'success': True})    
    except:
        return Response({'success': False, 'message': 'Cannot delete this user because some records depend on it'})

# =================================================== Permission ======================================================
@api_view(['GET'])
def searchPermission(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    permissions = Permission.objects.all()
    recordsTotal = permissions.count()

    permissions = permissions.filter(Q(name__contains=keyword) | Q(description__contains=keyword)).order_by('-createdDate')    
    recordsFiltered = permissions.count()
    permissions = permissions[start:start+length]
    data = PermissionSerializer(permissions, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })     

@api_view(['GET'])
def deletePermission(request, pk):
    try:
        permission = Permission.objects.get(pk=pk)
        permission.delete()
        return Response({'success': True})
    except:
        return Response({'success': False, 'message': 'Cannot delete this permission because some records depend on it'})

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

@api_view(['GET'])
def deleteDevice(request, pk):    
    try:
        device = Device.objects.get(pk=pk)    
        device.delete()
        return Response({'success': True})    
    except:
        return Response({'success': False, 'message': 'Cannot delete this device because some records depend on it'})


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
        item['location'] = f'{item["addressLine1"]}, {item["addressLine2"]}'
    
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

@api_view(['GET'])
def deleteLocation(request, pk):
    try:
        location = Location.objects.get(pk=pk)
        location.delete()
        return Response({'success': True})
    except:
        return Response({'success': False, 'message': 'Cannot delete this location because some records depend on it'})