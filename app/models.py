from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    dateTimeFormat = models.CharField(max_length=30, blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name='NFC Enabled', default=False)
    qrScanEnabled = models.BooleanField(verbose_name='QR Scanning Enabled', default=False)    
    active = models.BooleanField(default=False)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

class Permission(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    accessFunctions = models.CharField(max_length=1000, blank=True)
    viewFunctions = models.CharField(max_length=1000, blank=True)
    editFunctions = models.CharField(max_length=1000, blank=True)
    deleteFunctions = models.CharField(max_length=1000, blank=True)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Status:
        INVITED = 0
        REGISTERED = 1

    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.PROTECT)
    fullname = models.CharField(max_length=50, blank=True, null=True, unique=True)
    permissions = models.ManyToManyField(Permission)
    nfcEnabled = models.BooleanField(verbose_name='NFC Enabled', blank=True, null=True)
    qrScanEnabled = models.BooleanField(verbose_name='QR Scanning Enabled', blank=True, null=True)
    sharedLocation = models.BooleanField(verbose_name='Share location after each scan', blank=True, null=True)
    profilePicture = models.ImageField(upload_to='static/images', blank=True, null=True) 
    status = models.IntegerField(blank=True, null=True)   
    createdDate = models.DateTimeField(null=True)
    
    def __str__(self):
        if self.fullname:
            return self.fullname
        else:
            return self.username
   
    
class Location(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT,  blank=True, null=True)
    addressLine1 = models.CharField(max_length=100)
    addressLine2 = models.CharField(max_length=100)
    postCode = models.CharField(max_length=10)
    geoLocation = models.CharField(max_length=30, null=True)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.addressLine1}, {self.addressLine2}'

class Device(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, blank=True, null=True)    
    installationLocation = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)
    id1 = models.CharField(max_length=30)
    id2 = models.CharField(max_length=30)
    enabled = models.BooleanField()
    registeredDate = models.DateTimeField(blank=True, null=True)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.id1}-{self.id2}'

class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    device = models.ForeignKey(Device, on_delete=models.PROTECT)
    date = models.DateTimeField()
