import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in
from django.conf import settings

from datetime import datetime
import string
import random
import csv
import json
from threading import Thread

from .models import *
from .forms import *
from .mail_utils import sendAdminInvitationMail, sendInvitationMail

def logInHook(sender, user, request, **kwargs):
    logIn = LogIn()
    logIn.user = user
    logIn.date = datetime.now()
    logIn.save()

user_logged_in.connect(logInHook)

@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/_admin")
    else:
        if(request.user.status == User.Status.INVITED):
            return HttpResponseRedirect("/complete_registration")
        elif request.user.role and request.user.role.code in [settings.ROLES['ADMIN'], settings.ROLES['STAFF']]:
            return HttpResponseRedirect("/staff")
        else:
            return HttpResponseRedirect("/users")

def privacy(request):
    return render(request, 'privacy.html')
    
@login_required
def completeRegistration(request):
    form = RegistrationForm(initial={
            'fullname': request.user.fullname, 
            'organization': request.user.organization.name
        })

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.fullname = form.cleaned_data['fullname']
            user.password = make_password(form.cleaned_data['password'])
            user.status = User.Status.REGISTERED
            user.profilePicture = form.cleaned_data['profilePicture']
            user.save()

            if False:
                org = user.organization
                org.name = form.cleaned_data['organization']
                org.save()

            user = authenticate(username=user.username,
                                    password=form.cleaned_data['password'])
            login(request, user)

            return HttpResponseRedirect("/")

    return render(request, "registration/complete.html", {'form': form})

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
            if form.cleaned_data['profilePicture']:
                user.profilePicture = form.cleaned_data['profilePicture']
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