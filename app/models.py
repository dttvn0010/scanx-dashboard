from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

class Organization(models.Model):
    name = models.CharField(verbose_name=_('company.name') + ' * ', max_length=200, unique=True)
    adminUsername = models.CharField(max_length=150, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), default=False)
    geoLocationEnabled = models.BooleanField(verbose_name=_('geolocation.enabled'), default=False)    
    active = models.BooleanField(verbose_name=_('active'), default=False)
    createdDate = models.DateTimeField(null=True)
    createdBy = models.ForeignKey('app.User', null=True, on_delete=models.SET_NULL, related_name='createdBy')

    def __str__(self):
        return self.name

class Role(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)
        
    def __str__(self):
        return self.name

class Group(models.Model):
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name
        
    def hasFeaturePermission(self, featureCode):        
        featurePermissionSet = GroupFeaturePermission.objects.filter(group=self)
        return any(p.featureCode == featureCode for p in featurePermissionSet)

    def hasPagePermission(self, pageCode, actionCode):
        
        pagePermissionSet = GroupPagePermission.objects.filter(group=self)
        
        if actionCode != 'VIEW':
            return any(p.pageCode == pageCode and p.actionCode == actionCode for p in pagePermissionSet)
        else:
            return any(p.pageCode == pageCode for p in pagePermissionSet)

    def getViewHistoryGroups(self):
        viewed_groups = []
        viewHistoryPermissionSet = GroupViewHistoryPermission.objects.filter(group=self)
        
        for p in viewHistoryPermissionSet:
            if not any(x.code == p.viewGroup.code for x in viewed_groups):
                viewed_groups.append(p.viewGroup)
                
        return viewed_groups

class GroupFeaturePermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    featureCode = models.CharField(max_length=50)

class GroupPagePermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    pageCode = models.CharField(max_length=50)
    actionCode = models.CharField(max_length=30)

class GroupViewHistoryPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    viewGroup = models.ForeignKey(Group, related_name='viewGroup', on_delete=models.CASCADE, default=None)

class User(AbstractUser):
    class Status:
        INVITED = 0
        ACTIVE = 1
        LOCK_BY_SUPER_ADMIN = 1
        LOCK_BY_TENANT_ADMIN = 2

    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    fullname = models.CharField(verbose_name=_("fullname") + " (*)", max_length=50, blank=True, null=True)
    roles = models.ManyToManyField(Role, verbose_name=_("role") + " (*)")
    groups = models.ManyToManyField(Group, verbose_name=_("group"), blank=True, null=True)
    nfcEnabled = models.BooleanField(verbose_name=_('nfc.enabled'), blank=True, null=True)
    sharedLocation = models.BooleanField(verbose_name=_('geolocation.enabled'), blank=True, null=True)
    profilePicture = models.ImageField(upload_to='static/images', blank=True, null=True) 
    status = models.IntegerField(blank=True, null=True)   
    tmpPassword = models.CharField(max_length=30, blank=True, null=True)
    tmpPasswordExpired = models.DateTimeField(null=True)    
    isReseller = models.BooleanField(verbose_name=_('is.reseller'), default=False)
    createdDate = models.DateTimeField(null=True)
    
    @property
    def display(self):
        if self.fullname:
            return self.fullname
        else:
            return self.username

    def __str__(self):
        return self.display        

    def hasRole(self, roleCode):
        return any(role.code == roleCode for role in self.roles.all())

    def hasAnyRole(self, roleCodes):
        return any(self.hasRole(roleCode) for roleCode in roleCodes)

    def hasFeaturePermission(self, featureCode):
        if self.hasRole('ADMIN'):
            return True

        return any(group.hasFeaturePermission(featureCode) for group in self.groups.all())

    def hasPagePermission(self, pageCode, actionCode):
        if self.hasRole('ADMIN'):
            return True

        return any(group.hasPagePermission(pageCode, actionCode) for group in self.groups.all())

    def getViewHistoryGroups(self):
        if self.hasRole('ADMIN'):
            return Group.objects.filter(organization=self.organization)

        viewed_groups = []

        for group in self.groups.all():
            for viewed_group in group.getViewHistoryGroups():
                if not any(x.code == viewed_group.code for x in viewed_groups):
                    viewed_groups.append(viewed_group)
        
        return viewed_groups

    @property
    def viewed_groups(self):
        return self.getViewHistoryGroups()

    @property
    def viewed_users(self):
        if self.hasRole('ADMIN'):
            return User.objects.filter(organization=self.organization)
        else:
            return User.objects.filter(groups__in=self.getViewHistoryGroups())

    @property
    def view_users(self):
        return self.getViewHistoryGroups()

    @property
    def role_names(self):
        if self.is_superuser:
            return 'Super Admin'

        if self.isReseller:
            return 'Reseller'
            
        return ','.join([role.name for role in self.roles.all()])

    @property
    def role_codes(self):
        if self.is_superuser:
            return 'SUPER_ADMIN'

        if self.isReseller:
            return 'RESELLER'

        return ','.join([role.code for role in self.roles.all()])

    @property
    def is_tenant_admin(self):
        return self.hasRole('ADMIN')

    @property   
    def count_new_logs(self):
        logs = Log.objects.filter(~Q(performUser=self))
        if self.is_superuser:
            return logs.filter(~Q(viewUsers=self)).count()
        elif self.isReseller:
            organizations = Organization.objects.filter(createdBy=self)
            return logs.filter(organization__in=organizations).filter(~Q(viewUsers=self)).count()
        else:
            logs = logs.filter(organization=self.organization).filter(~Q(viewUsers=self))
            if not self.hasRole('ADMIN'):
                logs = logs.filter(performUser__in=self.view_users)
            
            return logs.count()
        
        return 0

    @property 
    def get_new_logs(self):
        logs = Log.objects.filter(~Q(performUser=self))
        if self.is_superuser:
            return logs.filter(~Q(viewUsers=self)).order_by('-actionDate')[:5]
        elif self.isReseller:
            organizations = Organization.objects.filter(createdBy=self)
            return logs.filter(organization__in=organizations).filter(~Q(viewUsers=self)).order_by('-actionDate')[:5]
        else:
            logs = logs.filter(organization=self.organization).filter(~Q(viewUsers=self))
            if not self.hasRole('ADMIN'):
                logs = logs.filter(performUser__in=self.view_users)
            
            return logs.order_by('-actionDate')[:5]
        
        return []
       
class Location(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,  blank=True, null=True)
    addressLine1 = models.CharField(verbose_name=_("addressLine1") + " (*)", max_length=100)
    addressLine2 = models.CharField(verbose_name=_("addressLine2"), max_length=100, blank=True, null=True)    
    city = models.CharField(verbose_name=_("city") + " (*)", max_length=50)
    postCode = models.CharField(verbose_name=_("postCode") + " (*)", max_length=10)
    createdDate = models.DateTimeField(null=True)
    createdBy = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

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
    enabled = models.BooleanField(default=True)
    createdDate = models.DateTimeField(null=True)   
    createdBy = models.ForeignKey(User, null=True, on_delete=models.SET_NULL) 

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
        DEVICE_DISABLED = 8
        SCAN_NOT_TIME_OUT_YET = 10

        messages =  {
            SUCCESS : _('check_in.status.success'),
            INCORRECT_MOBILE_TIME : _('check_in.status.incorrect.mobile.time'),
            INVALID_GPS_POSITION : _('check_in.status.invalid.gps.position'),
            INCORRECT_LOCATION: _('check_in.status.incorrect.location'),
            INVALID_DEVICE_CODE : _('check_in.status.invalid.device.code'),
            INCORRECT_DEVICE_UID: _('check_in.status.incorrect.device.uid'),
            DEVICE_NOT_REGISTERED : _('check_in.status.device.not.registered'),
            DEVICE_DISABLED: _('check_in.status.device.disabled'),
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
            DEVICE_DISABLED : _('check_in.mobile.message.device.disabled'),
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
    address = models.CharField(max_length=200, blank=True)   
    date = models.DateTimeField()
    status = models.IntegerField(null=True)

    @property
    def error_message(self):
        return CheckIn.Status.messages.get(self.status, '')

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

class LogAction(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def is_crud(self):
        return self.code in ['CREATE', 'UPDATE', 'DELETE']

    @property
    def is_login(self):
        return self.code == 'LOG_IN'

    @property
    def is_checkin(self):
        return self.code == 'CHECK_IN'

class LogConfig(models.Model):
    modelName = models.CharField(max_length=100, unique=True)
    logFields = models.CharField(max_length=1000, blank=True, null=True)
    displayFields = models.CharField(max_length=1000, blank=True, null=True)
    createNotifyTemplate = models.CharField(max_length=200, default='', blank=True)
    acquireNotifyTemplate = models.CharField(max_length=200, default='', blank=True)
    updateNotifyTemplate = models.CharField(max_length=200, default='', blank=True)
    releaseNotifyTemplate = models.CharField(max_length=200, default='', blank=True)
    deleteNotifyTemplate = models.CharField(max_length=200, default='', blank=True)

    def __str__(self):
        return self.modelName

class Log(models.Model):
    organization = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)
    modelName = models.CharField(max_length=100, default='')
    objectId = models.IntegerField(null=True)
    performUser = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.ForeignKey(LogAction, on_delete=models.PROTECT)
    actionDate = models.DateTimeField()
    preContent = models.TextField(null=True)
    postContent = models.TextField(null=True)
    viewUsers = models.ManyToManyField(User, related_name='view_users')
    
    def __str__(self):
        if self.action.code == 'CHECK_IN':
            return _('log.view.checkin.template') % (self.performUser.display)

        if self.action.code == 'LOG_IN':
            return _('log.view.login.template') % (self.performUser.display)

        return _('log.view.template') % (self.performUser.display, self.action.name, self.modelName)