from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def listOrgarnization(request):
    return render(request, "organizations.html")

@login_required
def listUnregisteredDevices(request):
    return render(request, "unregistered_devices.html")

@login_required
def listRegisteredDevices(request):
    return render(request, "registered_devices.html")