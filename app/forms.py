from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *
from django.utils.translation import gettext_lazy as _

class MyUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'fullname', 'email', 'organization')

class MyUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'fullname', 'email', 'organization')

class InitialSetupForm(forms.Form):
    fullname = forms.CharField(max_length=30)
    tempPassword = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30)
    password2 = forms.CharField(max_length=30)
    profilePicture = forms.ImageField(required=False)

    def clean_tempPassword(self):
        tempPassword = self.cleaned_data.get('tempPassword', '')
        user = User.objects.filter(username=self.initial.get('username')).first()
        ok = user and user.check_password('temp_' + tempPassword)
        
        if not ok:
            raise forms.ValidationError(_('incorrect.temporary.password'))

        return tempPassword

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 8:
            raise forms.ValidationError(_('password.too.short'))

        if password.isdigit():
            raise forms.ValidationError(_('password.cannot.be.all.digits'))

        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password != password2:
            raise forms.ValidationError(_('confirmed.password.not.match'))

        return password2

class UpdateAccountForm(forms.Form):
    email = forms.EmailField()
    fullname = forms.CharField(max_length=30)
    profilePicture = forms.ImageField(required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.initial.get('email') and User.objects.filter(email=email):
            raise forms.ValidationError('_("User with email") "%s" _("already exists")' % (email))

        return email

class ChangePasswordForm(forms.Form):
    current_pass = forms.CharField()
    password = forms.CharField()
    password2 = forms.CharField()

    def clean_current_pass(self):
        current_pass = self.cleaned_data.get('current_pass', '')
        
        if not self.initial['user'].check_password(current_pass):
            raise forms.ValidationError(_('incorrect.password'))
        
        return current_pass

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 8:
            raise forms.ValidationError(_('password.too.short'))

        if password.isdigit():
            raise forms.ValidationError(_('password.cannot.be.all.digits'))

        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password != password2:
            raise forms.ValidationError(_('confirmed.password.not.match'))

        return password2    

