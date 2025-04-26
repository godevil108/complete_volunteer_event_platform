from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class VolunteerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(null=True,max_length=100)
    age = models.IntegerField()
    profession = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    interests = models.TextField()
    pincode = models.CharField(max_length=10)
    address= models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

class EventManagerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=200,blank=True)  # Add this field
    phone_number = models.CharField(max_length=20)
    age = models.IntegerField()
    
    class Meta:
        verbose_name = 'Event Manager Profile'
        verbose_name_plural = 'Event Manager Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.organization_name}"

    def clean(self):
        # Add validation
        if self.age < 18:
            raise ValidationError({'age': 'Manager must be at least 18 years old'})
        
        # Validate phone number format
        if not re.match(r'^\+?1?\d{9,15}$', self.phone_number):
            raise ValidationError({'phone_number': 'Invalid phone number format'})

class Event(models.Model):
    manager = models.ForeignKey(EventManagerProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=100)
    address = models.TextField()
    pincode = models.CharField(max_length=10)
    image = models.ImageField(upload_to='event_images/')
    date = models.DateField()
    time = models.TimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    participants = models.ManyToManyField(User, related_name='participated_events', blank=True)
    participation_requests = models.ManyToManyField(User, related_name='requested_events', blank=True)
