import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required

from datetime import datetime
import string
import random
import csv
import json
from threading import Thread

from .models import *
from .forms import *
from .consts import MAIL_TEMPLATE_PATH
from .mail_utils import sendAdminInvitationMail, sendInvitationMail
from .permissions import PERMISSIONS


@login_required
def home(request):
    if request.user.is_superuser:
        return HttpResponseRedirect("/_admin")
    else:
        if(request.user.status == User.Status.INVITED):
            return HttpResponseRedirect("/complete_registration")
        elif request.user.is_staff:
            return HttpResponseRedirect("/staff")
        else:
            return HttpResponseRedirect("/users")

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


