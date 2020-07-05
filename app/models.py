from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Organization(models.Model):
    name = models.CharField(verbose_name=_('company.name') + ' * ', max_length=200, unique=True)
    adminUsername = models.CharField(max_length=150, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), default=False)
    qrScanEnabled = models.BooleanField(verbose_name=_('qr.scanning.enabled'), default=False)    
    geoLocationEnabled = models.BooleanField(verbose_name=_('geolocation.enabled'), default=False)    
    active = models.BooleanField(verbose_name=_('active'), default=False)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

class Role(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)
        
    def __str__(self):
        return self.name
        
class User(AbstractUser):
    class Status:
        INVITED = 0
        ACTIVE = 1
        LOCK_BY_SUPER_ADMIN = 1
        LOCK_BY_TENANT_ADMIN = 2

    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    fullname = models.CharField(verbose_name=_("fullname") + " (*)", max_length=50, blank=True, null=True)
    roles = models.ManyToManyField(Role, verbose_name=_("role") + " (*)")
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), blank=True, null=True)
    qrScanEnabled = models.BooleanField(verbose_name=_('qr.scanning.enabled'), blank=True, null=True)
    sharedLocation = models.BooleanField(verbose_name=_('geolocation.enabled'), blank=True, null=True)
    profilePicture = models.ImageField(upload_to='static/images', blank=True, null=True) 
    status = models.IntegerField(blank=True, null=True)   
    tmpPassword = models.CharField(max_length=30, blank=True, null=True)
    tmpPasswordExpired = models.DateTimeField(null=True)
    createdDate = models.DateTimeField(null=True)
    
    def __str__(self):
        if self.fullname:
            return self.fullname
        else:
            return self.username

    def hasRole(self, roleCode):
        return any(role.code == roleCode for role in self.roles.all())

    def hasAnyRole(self, roleCodes):
        return any(self.hasRole(roleCode) for roleCode in roleCodes)

    @property
    def role_names(self):
        return ','.join([role.name for role in self.roles.all()])

    @property
    def role_codes(self):
        return ','.join([role.code for role in self.roles.all()])

    @property
    def is_tenant_admin(self):
        return self.hasRole('ADMIN')
       
class Location(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,  blank=True, null=True)
    addressLine1 = models.CharField(verbose_name=_("addressLine1") + " (*)", max_length=100)
    addressLine2 = models.CharField(verbose_name=_("addressLine2"), max_length=100, blank=True, null=True)    
    city = models.CharField(verbose_name=_("city") + " (*)", max_length=50)
    postCode = models.CharField(verbose_name=_("postCode") + " (*)", max_length=10)
    createdDate = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.addressLine1}, {self.addressLine2}, {self.city}, {self.postCode}'

class Device(models.Model):
    class Status:
        ENABLED = 1
        LOCK_BY_SUPER_ADMIN = 2
        LOCK_BY_TENANT_ADMIN = 3

    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)        
    id1 = models.CharField(max_length=30, verbose_name=_("id1") + " (*)")
    id2 = models.CharField(max_length=30, verbose_name=_("id2") + " (*)")
    uid = models.CharField(max_length=50, verbose_name=_("uid"), blank=True, null=True, unique=True)
    installationLocation = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)    
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)
    description = models.CharField(max_length=500, verbose_name=_("description"), blank=True, null=True)
    registeredDate = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)   
    createdDate = models.DateTimeField(null=True)    

    def __str__(self):
        return f'{self.id1}-{self.id2}'

    @property
    def is_enabled(self):
        return self.status == Status.ENABLED

class CheckIn(models.Model):
    class Status:
        SUCCESS = 1
        INCORRECT_MOBILE_TIME = 2
        INVALID_GPS_POSITION = 3
        INCORRECT_LOCATION = 4
        INVALID_DEVICE_CODE = 5
        INCORRECT_DEVICE_UID = 6
        DEVICE_NOT_REGISTERED = 7
        SCAN_NOT_TIME_OUT_YET = 10

        messages =  {
            SUCCESS : _('check_in.status.success'),
            INCORRECT_MOBILE_TIME : _('check_in.status.incorrect.mobile.time'),
            INVALID_GPS_POSITION : _('check_in.status.invalid.gps.position'),
            INCORRECT_LOCATION: _('check_in.status.incorrect.location'),
            INVALID_DEVICE_CODE : _('check_in.status.invalid.device.code'),
            INCORRECT_DEVICE_UID: _('check_in.status.incorrect.device.uid'),
            DEVICE_NOT_REGISTERED : _('check_in.status.device.not.registered'),
            SCAN_NOT_TIME_OUT_YET : _('check_in.status.scan.not.time.out.yet'),
        }

        mobile_messages = {
            SUCCESS : _('check_in.mobile.message.success'),
            INCORRECT_MOBILE_TIME : _('check_in.mobile.message.incorrect.mobile.time'),
            INVALID_GPS_POSITION : _('check_in.mobile.message.invalid.gps.position'),
            INCORRECT_LOCATION: _('check_in.mobile.message.incorrect.location'),
            INVALID_DEVICE_CODE : _('check_in.mobile.message.invalid.device.code'),
            INCORRECT_DEVICE_UID: _('check_in.mobile.message.incorrect.device.uid'),
            DEVICE_NOT_REGISTERED : _('check_in.mobile.message.device.not.registered'),
            SCAN_NOT_TIME_OUT_YET : _('check_in.mobile.message.scan.not.time.out.yet'),
        }

    organization = models.ForeignKey(Organization, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, null=True, on_delete=models.SET_NULL)
    device = models.ForeignKey(Device, null=True, on_delete=models.SET_NULL)
    scanCode = models.CharField(max_length=50, blank=True, null=True)
    uid = models.CharField(max_length=50, blank=True, null=True)
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)    
    date = models.DateTimeField()
    status = models.IntegerField(null=True)

class LogIn(models.Model):
    organization = models.ForeignKey(Organization, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fromMobileApp = models.BooleanField()
    date = models.DateTimeField()

class SystemParameter(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    value = models.CharField(max_length=500, null=True, blank=True)
    min = models.CharField(max_length=50, null=True, blank=True)  
    max = models.CharField(max_length=50, null=True, blank=True) 
    maxLength = models.IntegerField(null=True, blank=True) 
    customizedByTenants = models.BooleanField() 

    def __str__(self):
        return self.name

    def getValue(self):
        if self.type == 'number':
            return float(self.value)
        return self.value

class TenantParameter(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)    
    parameter = models.ForeignKey(SystemParameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    def getValue(self):
        if self.parameter and self.parameter.type == 'number':
            return float(self.value)

        return self.value        

class MailTemplate(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    customizedByTenants = models.BooleanField() 

    def __str__(self):
        return self.name

class CRUDAction(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class LogConfig(models.Model):
    modelName = models.CharField(max_length=100, unique=True)
    logFields = models.CharField(max_length=1000, blank=True, null=True)
    displayFields = models.CharField(max_length=1000, blank=True, null=True)
    createNotifyTemplate = models.CharField(max_length=200, default='')
    acquireNotifyTemplate = models.CharField(max_length=200, default='')
    updateNotifyTemplate = models.CharField(max_length=200, default='')
    releaseNotifyTemplate = models.CharField(max_length=200, default='')
    deleteNotifyTemplate = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.modelName

class Log(models.Model):
    modelName = models.CharField(max_length=100, default='')
    performUser = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.ForeignKey(CRUDAction, on_delete=models.PROTECT)
    actionDate = models.DateTimeField()
    preContent = models.TextField(null=True)
    postContent = models.TextField(null=True)