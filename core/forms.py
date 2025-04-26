from django import forms
from django.contrib.auth.models import User
from .models import VolunteerProfile, EventManagerProfile, Event

class VolunteerSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            VolunteerProfile.objects.create(
                user=user,
                age=self.data['age'],
                profession=self.data['profession'],
                gender=self.data['gender'],
                interests=self.data['interests'],
                pincode=self.data['pincode']
            )
        return user

class EventManagerSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            EventManagerProfile.objects.create(
                user=user,
                age=self.data['age'],
                phone_number=self.data['phone']
            )
        return user

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'type', 'address', 'pincode', 'image', 'date', 'time']
