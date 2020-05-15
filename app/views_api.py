from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import *

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
    
    users = User.objects.all()
    recordsTotal = users.count()

    users = users.filter(Q(fullname__contains=keyword) | Q(email__contains=keyword)).order_by('-createdDate')
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


# =================================================== Device Group ======================================================
@api_view(['GET'])
def searchDeviceGroup(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    deviceGroups = DeviceGroup.objects.all()
    recordsTotal = deviceGroups.count()

    deviceGroups = deviceGroups.filter(Q(name__contains=keyword) | Q(description__contains=keyword)).order_by('-createdDate')    
    recordsFiltered = deviceGroups.count()
    deviceGroups = deviceGroups[start:start+length]
    data = DeviceGroupSerializer(deviceGroups, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })     

@api_view(['GET'])
def deleteDeviceGroup(request, pk):
    try:
        deviceGroup = DeviceGroup.objects.get(pk=pk)
        deviceGroup.delete()
        return Response({'success': True})
    except:
        return Response({'success': False, 'message': 'Cannot delete this device group because some records depend on it'})

# =================================================== Device ======================================================

@api_view(['GET'])
def searchUnregisteredDevice(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    devices = Device.objects.filter(status=Device.Status.UNREGISTERED)
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
    
    devices = Device.objects.filter(status=Device.Status.REGISTERED)
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

# =================================================== Location Group ======================================================
@api_view(['GET'])
def searchLocationGroup(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    locationGroups = LocationGroup.objects.all()
    recordsTotal = locationGroups.count()

    locationGroups = locationGroups.filter(Q(name__contains=keyword) | Q(description__contains=keyword)).order_by('-createdDate')    
    recordsFiltered = locationGroups.count()
    locationGroups = locationGroups[start:start+length]
    data = LocationGroupSerializer(locationGroups, many=True).data
    
    return Response({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": data
    })     

@api_view(['GET'])
def deleteLocationGroup(request, pk):
    try:
        locationGroup = LocationGroup.objects.get(pk=pk)
        locationGroup.delete()
        return Response({'success': True})
    except:
        return Response({'success': False, 'message': 'Cannot delete this location group because some records depend on it'})


# =================================================== Location ======================================================
@api_view(['GET'])
def searchLocation(request):
    draw = request.query_params.get('draw', 1)    
    keyword = request.query_params.get('search[value]', '')
    start = int(request.query_params.get('start', 0))
    length = int(request.query_params.get('length', 0))
    
    locations = Location.objects.all()
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