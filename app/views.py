from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .models import *
from .forms import *

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/admins")
    else:
        return HttpResponseRedirect("/users")

def signup(request):
   form = MyUserCreationForm()
   
   if request.method == 'POST':
       form = MyUserCreationForm(request.POST)
       if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username,
                                    password=request.POST['password1'])
            login(request, user)
            return redirect('home')

   return render(request, 'registration/signup.html', { 'form':  form})

# User
@login_required
def userViewTable(request):
    return render(request, "users/table_view.html")

@login_required
def userViewMap(request):
    return render(request, "users/map_view.html")

# Admin
@login_required
def adminViewOrganization(request):
    organizations = Organization.objects.all()
    for org in organizations:
        staff = User.objects.filter(organization=org).filter(is_staff=True).first()
        org.admin = staff
        org.userCount = User.objects.filter(organization=org).count()
        org.deviceCount = Device.objects.filter(organization=org).count()

    return render(request, "admins/organization/list.html", {"organizations" : organizations})

@login_required
def addOrganization(request):
    form = OrganizationForm()

    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

@login_required
def updateOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(instance=org)

    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('admin-home')

    return render(request, 'admins/organization/form.html', {'form': form})

@login_required
def deleteOrganization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    org.delete()
    return redirect("admin-home")

@login_required
def adminViewUnregisteredDevice(request):
    devices = Device.objects.filter(status=Device.Status.UNREGISTERED)
    return render(request, "admins/device/list_unregistered.html", {"devices": devices})

@login_required
def addUnregisteredDevice(request):
    form = UnRegisteredDeviceForm(organization=request.user.organization)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST)
        if form.is_valid():            
            device = form.save(commit=False)
            device.status = Device.Status.UNREGISTERED
            device.save()
            return redirect('admin-unregistered-device')

    return render(request, 'admins/device/form_unregistered.html', {'form': form})

@login_required
def updateUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = UnRegisteredDeviceForm(instance=device, organization=request.user.organization)

    if request.method == 'POST':
        form = UnRegisteredDeviceForm(request.POST, instance=device, organization=request.user.organization)

        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.UNREGISTERED
            device.save()            
            return redirect('admin-unregistered-device')

    return render(request, 'admins/device/form_unregistered.html', {'form': form})

@login_required
def deleteUnregisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-unregistered-device")

@login_required
def adminViewRegisteredDevice(request):
    devices = Device.objects.filter(status=Device.Status.REGISTERED)
    return render(request, "admins/device/list_registered.html", {"devices": devices})

@login_required
def addRegisteredDevice(request):
    form = RegisteredDeviceForm()

    if request.method == 'POST':
        form = RegisteredDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.REGISTERED
            device.save()   
            return redirect('admin-registered-device')

    return render(request, 'admins/device/form_registered.html', {'form': form})

@login_required
def updateRegisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form = RegisteredDeviceForm(instance=device)

    if request.method == 'POST':
        form = RegisteredDeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save(commit=False)
            device.status = Device.Status.REGISTERED
            device.save()
            return redirect('admin-registered-device')

    return render(request, 'admins/device/form_registered.html', {'form': form})

@login_required
def deleteRegisteredDevice(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.delete()
    return redirect("admin-registered-device")