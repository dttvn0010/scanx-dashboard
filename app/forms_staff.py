from django import forms
from .models import *

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('fullname', 'email', 'organization', 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'permissions')

    nfcEnabled = forms.BooleanField(label='NFC Enabled', required=False)
    qrScanEnabled = forms.BooleanField(label='QR Scanning Enabled', required=False)
    sharedLocation = forms.BooleanField(label='Share location after each scan', required=False)

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ('organization', 'createdDate',)
        
class DeviceCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        #self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    id1 = forms.CharField()
    id2 = forms.CharField()
    installationLocation = forms.ModelChoiceField(queryset=Location.objects.all())

    def clean(self):
        id1 = self.cleaned_data.get('id1')
        id2 = self.cleaned_data.get('id2')
        device = Device.objects.filter(id1=id1).filter(id2=id2).first()
        
        if not device:
            raise forms.ValidationError('This device does not existed')

        if device.organization:
            raise forms.ValidationError('This device is already registered')

        return self.cleaned_data

class DeviceChangeForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        #self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    installationLocation = forms.ModelChoiceField(queryset=Location.objects.all())
