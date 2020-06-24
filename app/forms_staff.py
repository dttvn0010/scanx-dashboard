from django import forms
from .models import *

class UserCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('fullname', 'email', 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'role')

    fullname = forms.CharField(max_length=30, label="Full Name * ")
    email = forms.EmailField(max_length=50, label="Email address * ")
    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
    sharedLocation = forms.BooleanField(label='Geo Location Enabled', required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email):
            raise forms.ValidationError('User with email "%s" already exists' % (email))

        return email


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ( 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'role')

    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
    sharedLocation = forms.BooleanField(label='Geo Location Enabled', required=False)

class UserAdminChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ( 'nfcEnabled', 'qrScanEnabled', 'sharedLocation')

    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
    sharedLocation = forms.BooleanField(label='Geo Location Enabled', required=False)    

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ('organization', 'createdDate',)
        
class DeviceCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    id1 = forms.CharField(label="Id1 * ")
    id2 = forms.CharField(label="Id2 * ")
    installationLocation = forms.ModelChoiceField(label="Installation Location * ", queryset=Location.objects.all())

    def clean(self):
        id1 = self.cleaned_data.get('id1')
        id2 = self.cleaned_data.get('id2')
        device = Device.objects.filter(id1=id1).filter(id2=id2).first()
        
        if not device:
            raise forms.ValidationError('This device does not exist')

        if device.organization:
            raise forms.ValidationError('This device is already registered')

        return self.cleaned_data

class DeviceChangeForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    installationLocation = forms.ModelChoiceField(label="Installation Location * ",
                                queryset=Location.objects.all())


class OrganizationChangeForm(forms.Form):
    name = forms.CharField(label="Organization Name * ")
    description = forms.CharField(label="Detail Information", required=False, 
                        widget=forms.Textarea(attrs={'rows':4}))
    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
