from .models import *
from django.apps import apps
from django.utils import timezone

import json
import traceback

def dumpObject(obj, fields):
    data = {}
    for key in fields:
        value = getattr(obj, key)
        if value and value.__class__.__name__ in  ['int', 'bool', 'float', 'str', 'datetime']:
            data[key] = value
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
        log.modelName = modelName
        log.performUser = user
        log.action = CRUDAction.objects.get(code=actionCode)
        log.actionDate = timezone.now()
        log.preContent = dumpObject(oldObj, logFields) if oldObj else ''
        log.postContent = dumpObject(newObj, logFields) if newObj else ''
        log.save()
    except:
        traceback.print_exc()