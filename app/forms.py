from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class MyUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'fullname', 'email', 'organization')

class MyUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'fullname', 'email', 'organization')


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

class UnRegisteredDeviceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)        
        
        if organization:            
            self.fields['deviceGroup'].queryset = DeviceGroup.objects.filter(organization=organization)
        else:
            self.fields['deviceGroup'].queryset = DeviceGroup.objects.all()
        
    class Meta:
        model = Device
        exclude = ('status', 'registeredDate')

class RegisteredDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        exclude = ('status',)