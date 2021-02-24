from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _

class UserCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('fullname', 'email', 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'groups')

    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['groups'].queryset = Group.objects.filter(organization=organization)

    fullname = forms.CharField(max_length=30, label=_("fullname") + " (*)")
    email = forms.EmailField(max_length=50, label=_("email.address") + " (*)")
    nfcEnabled = forms.BooleanField(label=_('nfc.enabled'), required=False)
    qrScanEnabled = forms.BooleanField(label=_('qr.scanning.enabled'), required=False)
    sharedLocation = forms.BooleanField(label=_('geolocation.enabled'), required=False)
    roleIds = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email):
            raise forms.ValidationError(f'{_("user.with.email")} "%s" {_("already.exists")}' % (email))

        return email

class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ( 'nfcEnabled', 'qrScanEnabled', 'sharedLocation', 'groups')

    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['groups'].queryset = Group.objects.filter(organization=organization)

    nfcEnabled = forms.BooleanField(label=_('nfc.enabled'), required=False)
    qrScanEnabled = forms.BooleanField(label=_('qr.scanning.enabled'), required=False)
    sharedLocation = forms.BooleanField(label=_('geolocation.enabled'), required=False)
    roleIds = forms.CharField(widget=forms.HiddenInput(), required=False)

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ('organization', 'createdDate',)
        
class DeviceCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    id1 = forms.CharField(label=_('id1') + " (*)")
    id2 = forms.CharField(label=_('id2') + " (*)")
    installationLocation = forms.ModelChoiceField(label=_("installation.location") + " (*)", queryset=Location.objects.all())
    description = forms.CharField(label=_('description'), required=False, widget=forms.Textarea(attrs={'rows':2}))

    def clean(self):
        id1 = self.cleaned_data.get('id1')
        id2 = self.cleaned_data.get('id2')
        device = Device.objects.filter(id1=id1).filter(id2=id2).first()
        
        if not device:
            raise forms.ValidationError(_('this.device.does.not.exist'))

        if device and not device.uid:
            raise forms.ValidationError(_('this.device.not.set.uid.yet'))

        if device.organization:
            raise forms.ValidationError(_('this.device.is.already.registered'))

        return self.cleaned_data

class DeviceChangeForm(forms.Form):
    def __init__(self, *args, **kwargs):        
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)  
        self.fields['installationLocation'].queryset = Location.objects.filter(organization=organization)

    installationLocation = forms.ModelChoiceField(label=_("installation.location") + " (*)",
                                queryset=Location.objects.all())

    description = forms.CharField(label=_('description'), required=False, widget=forms.Textarea(attrs={'rows':2}))

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('organization',)

class OrganizationChangeForm(forms.Form):
    name = forms.CharField(label=_("organization.name") + " (*)")
    description = forms.CharField(label=_("detail.information"), required=False, 
                        widget=forms.Textarea(attrs={'rows':4}))
    nfcEnabled = forms.BooleanField(label=_('nfc.enabled'), required=False)
    qrScanEnabled = forms.BooleanField(label=_('qr.scanning.enabled'), required=False)
