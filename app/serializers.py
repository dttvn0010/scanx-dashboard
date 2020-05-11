from rest_framework.serializers import ModelSerializer, CharField, DateTimeField
from .models import *

class OrganizationSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class DeviceSerializer(ModelSerializer):
    deviceTypeName = CharField(source='deviceType.name')
    organizationName = CharField(source='organization.name', default="")
    registeredDate = DateTimeField(format="%Y-%m-%d", required=False, read_only=True)

    class Meta:
        model = Device
        fields = ('id', 'organizationName', 'deviceTypeName', 'id1', 'id2', 'enabled', 'registeredDate') 