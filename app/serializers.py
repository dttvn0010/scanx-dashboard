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

class DeviceSerializer(ModelSerializer):
    organizationName = CharField(source='organization.name', default="")
    addressLine1 = CharField(source='installationLocation.addressLine1', default="")
    addressLine2 = CharField(source='installationLocation.addressLine2', default="")
    registeredDate = DateTimeField(format="%d %b,%Y", required=False, read_only=True)


    class Meta:
        model = Device
        fields = ('id', 'addressLine1', 'addressLine2', 'organizationName', 'id1', 'id2', 'enabled', 'registeredDate') 

class LocationSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'        

class CheckInSerializer(ModelSerializer):    
    userFullName = CharField(source='user.fullname', default="")
    username = CharField(source='user.username', default="")
    addressLine1 = CharField(source='location.addressLine1', default="")
    addressLine2 = CharField(source='location.addressLine2', default="")
    geoLocation = CharField(source='location.geoLocation', default="")
    date = DateTimeField(format="%d/%m/%Y %H:%M:%S", required=False, read_only=True)
    class Meta:
        model = CheckIn
        fields = ('username', 'userFullName', 'addressLine1', 'addressLine2', 'geoLocation', 'date',)

class LogInSerializer(ModelSerializer):    
    userFullName = CharField(source='user.fullname', default="")
    username = CharField(source='user.username', default="")
    date = DateTimeField(format="%d/%m/%Y %H:%M:%S", required=False, read_only=True)
    class Meta:
        model = CheckIn
        fields = ('username', 'userFullName', 'date',)        