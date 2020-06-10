import os
import sys

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from datetime import datetime
import string
import random
import csv
import json
from threading import Thread
from io import BytesIO
from PIL import Image

from .models import *
from .forms import *
from .mail_utils import sendAdminInvitationMail, sendInvitationMail

def logInHook(sender, user, request, **kwargs):
    logIn = LogIn()
    logIn.user = user
    logIn.date = datetime.now()
    logIn.save()

user_logged_in.connect(logInHook)

def initialSetup(request):
    email = request.GET.get('email')
    user = User.objects.filter(username=email).first() if email else None
    if not user or user.status != User.Status.INVITED:
        return redirect('home')

    form = InitialSetupForm(initial={
            'fullname': user.fullname
        })

    if request.method == 'POST':
        form = InitialSetupForm(request.POST, request.FILES, initial={'username': user.username})
        if form.is_valid():
            user.fullname = form.cleaned_data['fullname']
            user.password = make_password(form.cleaned_data['password'])
            user.status = User.Status.REGISTERED
            
            profilePicture = form.cleaned_data.get('profilePicture')
            if profilePicture and profilePicture.name != '' :
                user.profilePicture = resizeProfileImage(profilePicture)

            user.save()

            user = authenticate(username=user.username,
                                    password=form.cleaned_data['password'])
            login(request, user)

            return HttpResponseRedirect("/")

    return render(request, "registration/initial_setup.html", {'form': form})

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/_admin")
    else:
        if(request.user.status == User.Status.INVITED):
            return HttpResponseRedirect("/accounts/login")
        elif request.user.role and request.user.role.code in [settings.ROLES['ADMIN'], settings.ROLES['STAFF']]:
            return HttpResponseRedirect("/staff")
        else:
            return HttpResponseRedirect("/users")

def privacy(request):
    return render(request, 'privacy.html')

def support(request):
    return render(request, 'support.html')

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

def resizeProfileImage(imgField):
    imageFile = BytesIO(imgField.read())
    image = Image.open(imageFile)
    w, h = image.size
    sz = min(w, h, 300)
    
    image = image.resize((sz, sz), Image.ANTIALIAS)

    output = BytesIO()
    image.save(output, 'JPEG', quality=90)
    fileName = f"{imgField.name.split('.')[0]}.jpg"
    return InMemoryUploadedFile(output,'ImageField', fileName , 'image/jpeg', sys.getsizeof(output), None)
    
def updateAccount(request):
    form = UpdateAccountForm(initial={
            'fullname': request.user.fullname, 
            'email': request.user.email
        })

    if request.method == 'POST':
        form = UpdateAccountForm(request.POST, request.FILES, initial={'email': request.user.email})
        if form.is_valid():
            user = request.user
            user.username = form.cleaned_data['email']
            user.email = form.cleaned_data['email']
            user.fullname = form.cleaned_data['fullname']
            profilePicture = form.cleaned_data.get('profilePicture')
            if profilePicture and profilePicture.name != '' :
                user.profilePicture = resizeProfileImage(profilePicture)
            user.save()
            
            return HttpResponseRedirect("/")

    return render(request, 'profile/update_account.html', {'form': form})

def changePassword(request):
    form = ChangePasswordForm(initial={'user': request.user})

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            user = request.user
            user.password = make_password(form.cleaned_data['password'])
            user.save()
            
            user = authenticate(username=user.username,
                                    password=form.cleaned_data['password'])
            login(request, user)

            return HttpResponseRedirect("/")

    return render(request, 'profile/change_password.html', {'form': form})