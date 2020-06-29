from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _

class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

    adminName = forms.CharField(max_length=30, label=_("admin.name") + " * ")
    adminEmail = forms.EmailField(max_length=50, label=_("admin.email") + " * ")

    def clean_adminEmail(self):
        email = self.cleaned_data.get('adminEmail')
        if User.objects.filter(email=email):
            raise forms.ValidationError(f'{_("user.with.email")} "%s" {_("already.exists")}' % (email))

        return email

class OrganizationChangeForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'nfcEnabled', 'qrScanEnabled', 'active')

class UnRegisteredDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ('id1', 'id2')

    def clean_uid(self):
        uid = self.cleaned_data.get('uid', '')

        if uid != '':
            device = Device.objects.filter(uid=uid).first()
            if device and (self.instance == None or self.instance.id != device.id):
                raise forms.ValidationError(f'{_("device.with")} {_("uid")}={uid} {_("already.exists")}')

        return uid

    def clean(self):
        id1 = self.cleaned_data.get('id1')
        id2 = self.cleaned_data.get('id2')
        device = Device.objects.filter(id1=id1).filter(id2=id2).first()

        if device and (self.instance == None or self.instance.id != device.id):
            raise forms.ValidationError(f'{_("device.with")} {_("id1")}={id1} & {_("id2")}={id2} {_("already.exists")}')

        return self.cleaned_data

