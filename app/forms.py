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

class RegistrationForm(forms.Form):
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

class UpdateAccountForm(forms.Form):
    email = forms.EmailField()
    fullname = forms.CharField(max_length=30)
    profilePicture = forms.ImageField(required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.initial.get('email') and User.objects.filter(email=email):
            raise forms.ValidationError('User with email "%s" already exists' % (email))

        return email

class ChangePasswordForm(forms.Form):
    current_pass = forms.CharField()
    password = forms.CharField()
    password2 = forms.CharField()

    def clean_current_pass(self):
        current_pass = self.cleaned_data.get('current_pass', '')
        
        if not self.initial['user'].check_password(current_pass):
            raise forms.ValidationError('Incorrect password')
        
        return current_pass

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

