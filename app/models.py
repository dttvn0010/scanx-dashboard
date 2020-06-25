from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    name = models.CharField(verbose_name=_('company.name') + ' * ', max_length=200, unique=True)
    adminUsername = models.CharField(max_length=150, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    dateTimeFormat = models.CharField(max_length=30, blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), default=False)
    qrScanEnabled = models.BooleanField(verbose_name=_('qr.scanning.enabled'), default=False)    
    active = models.BooleanField(verbose_name=_('active'), default=False)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

class Role(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    level = models.IntegerField()
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ["level"]
        
    def __str__(self):
        st = self.name

        if self.description:
            st += f'({self.description})'
        
        return st
        

class User(AbstractUser):
    class Status:
        INVITED = 0
        REGISTERED = 1

    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    fullname = models.CharField(verbose_name=_("fullname") + " * ", max_length=50, blank=True, null=True)
    role = models.ForeignKey(Role, verbose_name=_("role") + " * ", null=True, on_delete=models.SET_NULL)
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), blank=True, null=True)
    qrScanEnabled = models.BooleanField(verbose_name=_('qr.scanning.enabled'), blank=True, null=True)
    sharedLocation = models.BooleanField(verbose_name=_('geolocation.enabled'), blank=True, null=True)
    profilePicture = models.ImageField(upload_to='static/images', blank=True, null=True) 
    status = models.IntegerField(blank=True, null=True)   
    createdDate = models.DateTimeField(null=True)
    
    def __str__(self):
        if self.fullname:
            return self.fullname
        else:
            return self.username
   
    
class Location(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,  blank=True, null=True)
    addressLine1 = models.CharField(verbose_name=_("addressLine1") + " * ", max_length=100)
    addressLine2 = models.CharField(verbose_name=_("addressLine2"), max_length=100, blank=True, null=True)    
    city = models.CharField(verbose_name=_("city") + " * ", max_length=50)
    postCode = models.CharField(verbose_name=_("postCode") + " * ", max_length=10)
    geoLocation = models.CharField(verbose_name=_("map.coordinates") + " * ", max_length=30, null=True)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.addressLine1}, {self.addressLine2}, {self.city}, {self.postCode}'

class Device(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)    
    installationLocation = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
    id1 = models.CharField(max_length=30, verbose_name=_("id1") + " * ")
    id2 = models.CharField(max_length=30, verbose_name=_("id2") + " * ")
    enabled = models.BooleanField()
    registeredDate = models.DateTimeField(blank=True, null=True)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.id1}-{self.id2}'

class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, null=True, on_delete=models.SET_NULL)
    geoLocation = models.CharField(max_length=50, null=True)
    date = models.DateTimeField()

class LogIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()

class Parameter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    value = models.CharField(max_length=500, null=True, blank=True)
    min = models.CharField(max_length=50, null=True, blank=True)  
    max = models.CharField(max_length=50, null=True, blank=True)  

    def __str__(self):
        return self.name
