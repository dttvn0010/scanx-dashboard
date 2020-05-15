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

class MyUserRegistrationForm(forms.Form):
    fullname = forms.CharField(max_length=30, label='Your name')
    organization = forms.CharField(max_length=200, label='Your organization name')
    password = forms.CharField(max_length=30, widget=forms.PasswordInput, label='Enter a new password')
    password2 = forms.CharField(max_length=30, widget=forms.PasswordInput, label='Confirmed Password')
    profilePicture = forms.ImageField(label="Choose a profile picture", required=False)

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 8:
            raise forms.ValidationError('Password too short')

        if password.isdigit():
            raise forms.ValidationError('Password cannot be all digits')

        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password != password2:
            raise forms.ValidationError('Confirmed password does not match')

        return password2

class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

    adminName = forms.CharField(max_length=30, label="Admin name")
    adminEmail = forms.EmailField(max_length=50, label="Admin email")

    def clean_adminName(self):
        adminName = self.cleaned_data.get('adminName')
        if User.objects.filter(fullname=adminName):
            raise forms.ValidationError('User with name "%s" already existed' % (adminName))

        return adminName

    def clean_adminEmail(self):
        email = self.cleaned_data.get('adminEmail')
        if User.objects.filter(email=email):
            raise forms.ValidationError('User with email "%s" already existed' % (email))

        return email

class OrganizationChangeForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('fullname', 'email', 'organization', 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'permissions')

    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
    sharedLocation = forms.BooleanField(label='Share location after each scan', required=False)

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        exclude = ('createdDate',)
    
    accessFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    viewFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    editFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    deleteFunctions = forms.CharField(widget=forms.HiddenInput, required=False)

class DeviceTypeForm(forms.ModelForm):
    class Meta:
        model = DeviceType
        exclude = ('createdDate',)


class DeviceGroupForm(forms.ModelForm):
    class Meta:
        model = DeviceGroup
        exclude = ('createdDate',)

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
        exclude = ('status', 'createdDate', 'registeredDate', )

class RegisteredDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        exclude = ('status', 'createdDate')

    registeredDate = forms.DateTimeField(input_formats=['%d %b,%Y'], 
                        widget=forms.widgets.DateTimeInput(format="%d %b,%Y"), 
                        label='Registered date', required=False)


class LocationGroupForm(forms.ModelForm):
    class Meta:
        model = LocationGroup
        exclude = ('createdDate',)

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ('createdDate',)
    
