from django.urls import path
from .views import *

urlpatterns = [
    path("", listOrgarnization),
    path("unregistered_devices", listUnregisteredDevices),
    path("registered_devices", listRegisteredDevices)
]