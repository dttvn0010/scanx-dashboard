from django import forms
from .models import *

class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

    adminName = forms.CharField(max_length=30, label="Admin name")
    adminEmail = forms.EmailField(max_length=50, label="Admin email")

    def clean_adminName(self):
        adminName = self.cleaned_data.get('adminName')
        if User.objects.filter(fullname=adminName):
            raise forms.ValidationError('User with name "%s" already exists' % (adminName))

        return adminName

    def clean_adminEmail(self):
        email = self.cleaned_data.get('adminEmail')
        if User.objects.filter(email=email):
            raise forms.ValidationError('User with email "%s" already exists' % (email))

        return email

class OrganizationChangeForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        exclude = ('createdDate',)
    
    accessFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    viewFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    editFunctions = forms.CharField(widget=forms.HiddenInput, required=False)
    deleteFunctions = forms.CharField(widget=forms.HiddenInput, required=False)

class UnRegisteredDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ('id1', 'id2')

    def clean(self):
        id1 = self.cleaned_data.get('id1')
        id2 = self.cleaned_data.get('id2')
        device = Device.objects.filter(id1=id1).filter(id2=id2).first()

        if device and (self.instance == None or self.instance.id != device.id):
            raise forms.ValidationError(f'Device with id1={id1} & id2={id2} already exists')

        return self.cleaned_data

