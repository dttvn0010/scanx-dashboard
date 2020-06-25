from .models import *

def getSystemParamValue(key, defaultValue=None):
    param = Parameter.objects.filter(key=key).first()
    
    if param and param.value:
        return param.getValue()
    
    return defaultValue

def getTenantParamValue(key, organization, defaultValue=None):
    param = Parameter.objects.filter(key=key).first()

    if param:
        tenantParam = TenantParameter.objects.filter(organization=organization,parameter=param).first()
        if tenantParam and tenantParam.value:
            return tenantParam.getValue()
        elif param.value:
            return param.getValue()

    return defaultValue