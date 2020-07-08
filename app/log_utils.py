from .models import *
from django.apps import apps
from django.utils import timezone

import json
import traceback

def dumpObject(obj, fields):
    data = {}
    for key in fields:
        value = getattr(obj, key)
        if value != None and value.__class__.__name__ in  ['int', 'bool', 'float', 'str']:
            data[key] = value
        elif value != None and value.__class__.__name__ == 'datetime':
            data[key] = value.strftime('%d/%m/%Y %H:%M:%S')
        else:
            data[key] = str(value) if value else None

    return json.dumps(data)

def getLogFields(modelName):
    logConfig = LogConfig.objects.filter(modelName=modelName).first()
    if logConfig and logConfig.logFields:
        return logConfig.logFields.split(',')
    
    return []

def logAction(actionCode, user, oldObj, newObj):
    try:
        modelName = newObj.__class__.__name__ if newObj else oldObj.__class__.__name__
        logFields = getLogFields(modelName)
        if not logFields:
            return

        log = Log()

        if oldObj and hasattr(oldObj, 'id'):
            log.objectId = oldObj.id
        elif newObj and hasattr(newObj, 'id'):
            log.objectId = newObj.id

        log.modelName = modelName
        log.performUser = user
        log.organization = user.organization
        log.action = CRUDAction.objects.get(code=actionCode)
        log.actionDate = timezone.now()
        log.preContent = dumpObject(oldObj, logFields) if oldObj else ''
        log.postContent = dumpObject(newObj, logFields) if newObj else ''
        log.save()
    except:
        traceback.print_exc()