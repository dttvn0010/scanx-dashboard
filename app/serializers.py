from rest_framework.serializers import ModelSerializer, CharField, DateTimeField
from .models import *

class OrganizationSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PermissionSerializer(ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class DeviceGroupSerializer(ModelSerializer):
    class Meta:
        model = DeviceGroup
        fields = '__all__'

class DeviceSerializer(ModelSerializer):
    deviceTypeName = CharField(source='deviceType.name')
    organizationName = CharField(source='organization.name', default="")
    registeredDate = DateTimeField(format="%d %b,%Y", required=False, read_only=True)

    class Meta:
        model = Device
        fields = ('id', 'organizationName', 'deviceTypeName', 'id1', 'id2', 'enabled', 'registeredDate') 

class LocationGroupSerializer(ModelSerializer):
    class Meta:
        model = LocationGroup
        fields = '__all__'

class LocationSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'        