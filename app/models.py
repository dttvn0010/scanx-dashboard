from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    dateTimeFormat = models.CharField(max_length=30, blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name='NFC Enabled', default=False)
    qrScanEnabled = models.BooleanField(verbose_name='QR Scanning Enabled', default=False)    
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class User(AbstractUser):
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.PROTECT)
    fullname = models.CharField(max_length=50, blank=True, null=True, unique=True)
    nfcEnabled = models.BooleanField(verbose_name='NFC Enabled', blank=True, null=True)
    qrScanEnabled = models.BooleanField(verbose_name='QR Scanning Enabled', blank=True, null=True)
    sharedLocation = models.BooleanField(verbose_name="Share location after each scan", blank=True, null=True)
    profilePicture = models.ImageField(upload_to='static/images', blank=True, null=True)    
    

    def __str__(self):
        if self.fullname:
            return self.fullname
        else:
            return self.username

class LocationGroup(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Location(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    locationGroup = models.ForeignKey(LocationGroup, on_delete=models.PROTECT)
    addressLine1 = models.CharField(max_length=100)
    addressLine2 = models.CharField(max_length=100)
    postCode = models.CharField(max_length=10)
    longitude = models.FloatField()
    latitude = models.FloatField()

    def __str__(self):
        return f'{self.addressLine1}, {self.addressLine2}'

class DeviceGroup(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class DeviceType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class Device(models.Model):
    class Status:
        UNREGISTERED = 0
        REGISTERED = 1

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)    
    deviceGroup = models.ForeignKey(DeviceGroup, on_delete=models.PROTECT)
    installationLocation = models.ForeignKey(Location, on_delete=models.PROTECT)
    locationDescription = models.CharField(max_length=500, blank=True, null=True)
    deviceType = models.ForeignKey(DeviceType, blank=True, null=True, on_delete=models.PROTECT)
    id1 = models.CharField(max_length=30)
    id2 = models.CharField(max_length=30)
    status = models.IntegerField(blank=True, null=True)
    enabled = models.BooleanField()
    registeredDate = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.id1}-{self.id2}'