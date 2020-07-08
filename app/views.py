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
from django.utils import timezone

from datetime import datetime, timedelta
import string
import random
import csv
import json
from threading import Thread
from io import BytesIO
from PIL import Image
import numpy as np

from .models import *
from .forms import *
from .mail_utils import sendAdminInvitationMail, sendInvitationMail, sendResetPasswordMail
from .user_utils import genPassword
from .log_utils import logAction

def logInHook(sender, user, request, **kwargs):
    logIn = LogIn()
    logIn.fromMobileApp = False
    logIn.user = user
    logIn.organization = user.organization
    logIn.date = timezone.now()
    logIn.save()
    print('=====================')
    logAction('CREATE', user, None, logIn)

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
            user.status = User.Status.ACTIVE
            
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
        elif request.user.hasRole('ADMIN') or request.user.hasRole('STAFF'):
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

def forgotPassword(request):
    sent = False
    form = ForgotPasswordForm()
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(username=form.cleaned_data.get('email'))
            user.tmpPassword = genPassword(20)
            user.tmpPasswordExpired = timezone.now() + timedelta(days=1)
            user.save()
            sendResetPasswordMail(user.fullname, user.email, user.tmpPassword)
            return render(request, 'registration/forgot_password_sent.html', {'email': user.email})

    return render(request, 'registration/forgot_password.html', {'sent': sent, 'form': form})

def resetPassword(request):
    if request.method == 'GET':
        form = ResetPasswordForm()
        email = request.GET.get('email')
        token = request.GET.get('token')
        user = User.objects.filter(username=email).first()
        if not user or user.tmpPassword != token or not user.tmpPassword:
            return render(request, 'registration/reset_password.html', {'invalid': True, 'form': form})
        
        if timezone.now() > user.tmpPasswordExpired:
            return render(request, 'registration/reset_password.html', {'expired': True, 'form': form})

        return render(request, 'registration/reset_password.html', {'email': email, 'form': form})

    else:
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(username=form.cleaned_data['email']).first()
            user.password = make_password(form.cleaned_data['password'])
            user.tmpPassword = ''
            user.tmpPasswordExpired = None
            user.save()
            
            user = authenticate(username=user.username,
                                    password=form.cleaned_data['password'])
            login(request, user)

            return HttpResponseRedirect("/")
        else:
            email = request.POST.get('email')
            return render(request, 'registration/reset_password.html', {'email': email, 'form': form})


def resizeProfileImage(imgField):
    imageFile = BytesIO(imgField.read())
    image = Image.open(imageFile)
    w, h = image.size
    sz = min(w, h, settings.PROFILE_IMAGE_SIZE)

    image_data = np.array(image)
    image_data = image_data[:,:,:3]

    if h > w:
        image_data = image_data[:w]
    
    image = Image.fromarray(image_data).resize((sz, sz), Image.ANTIALIAS)

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