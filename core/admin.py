from django.contrib import admin
from .models import VolunteerProfile, EventManagerProfile, Event

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'profession', 'gender', 'pincode')
    search_fields = ('user__username', 'profession', 'pincode')

@admin.register(EventManagerProfile)
class EventManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'age')
    search_fields = ('user__username', 'phone_number')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'manager', 'date', 'time', 'pincode')
    search_fields = ('name', 'type', 'pincode')
    list_filter = ('type', 'date')