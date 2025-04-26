from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import VolunteerProfile, EventManagerProfile, Event
from django.contrib.auth.decorators import login_required
from .forms import VolunteerSignupForm, EventManagerSignupForm, EventForm
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import F, Value, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from math import radians, cos, sin, asin, sqrt
import math

def index(request):
    return render(request, 'core/index.html')

def volunteer_signup(request):
    if request.method == 'POST':
        form = VolunteerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('volunteer_dashboard')
    else:
        form = VolunteerSignupForm()
    return render(request, 'core/volunteer_signup.html', {'form': form})

def volunteer_login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('volunteer_dashboard')
    return render(request, 'core/volunteer_login.html')

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    # Haversine formula
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return round(c * r, 2)

@login_required
def volunteer_dashboard(request):
    # Get the current date and next day date
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Get volunteer profile and interests
    volunteer_profile = get_object_or_404(VolunteerProfile, user=request.user)
    user_interests = volunteer_profile.interests.lower().split(',') if volunteer_profile.interests else []
    user_interests = [interest.strip() for interest in user_interests]
    
    # Get volunteer location
    volunteer = request.user.volunteerprofile
    user_lat = volunteer.latitude
    user_lon = volunteer.longitude
    
    # Get all upcoming events
    upcoming_events = Event.objects.filter(date__gte=today).order_by('date')
    
    # Prepare different priority categories
    tomorrow_events = []
    interest_events = []
    nearby_2km = []
    nearby_5km = []
    nearby_10km = []
    other_events = []
    
    for event in upcoming_events:
        # Get event coordinates (assuming they're stored in the database or in hidden fields)
        event_lat = float(event.latitude) if hasattr(event, 'latitude') and event.latitude else 0
        event_lng = float(event.longitude) if hasattr(event, 'longitude') and event.longitude else 0
        
        # Calculate distance if coordinates are available
        distance = None
        if user_lat and user_lon and event_lat and event_lng:
            distance = calculate_distance(user_lat, user_lon, event_lat, event_lng)
            event.distance = round(distance, 1)  # Round to 1 decimal place
        else:
            event.distance = None
        
        # Check if event is happening tomorrow
        if event.date == tomorrow:
            tomorrow_events.append(event)
            continue
        
        # Check if event matches user interests
        event_type_lower = event.type.lower()
        if any(interest in event_type_lower for interest in user_interests):
            interest_events.append(event)
            continue
            
        # Check proximity
        if distance is not None:
            if distance <= 2:
                nearby_2km.append(event)
            elif distance <= 5:
                nearby_5km.append(event)
            elif distance <= 10:
                nearby_10km.append(event)
            else:
                other_events.append(event)
        else:
            other_events.append(event)
    
    # Sort each category by date
    for event_list in [tomorrow_events, interest_events, nearby_2km, nearby_5km, nearby_10km, other_events]:
        event_list.sort(key=lambda x: x.date)
    
    # Events categorized with labels
    categorized_events = [
        {"category": "Happening Tomorrow", "events": tomorrow_events, "badge_class": "bg-danger"},
        {"category": "Matching Your Interests", "events": interest_events, "badge_class": "bg-success"},
        {"category": "Within 2km", "events": nearby_2km, "badge_class": "bg-primary"},
        {"category": "Within 5km", "events": nearby_5km, "badge_class": "bg-info"},
        {"category": "Within 10km", "events": nearby_10km, "badge_class": "bg-warning"},
        {"category": "Other Events", "events": other_events, "badge_class": "bg-secondary"}
    ]
    
    # Remove empty categories
    categorized_events = [cat for cat in categorized_events if cat["events"]]
    
    # Calculate distance for each event if user has location
    if user_lat and user_lon:
        for category in categorized_events:
            for event in category['events']:
                if event.latitude and event.longitude:
                    event.distance = calculate_distance(
                        user_lat, user_lon,
                        event.latitude, event.longitude
                    )
                else:
                    event.distance = 'unknown'
    
    # Get all events in a flattened list for filter operations
    all_events = []
    for category in categorized_events:
        all_events.extend(category["events"])
    
    # Get user's interests from their profile
    user_interests = request.user.volunteerprofile.interests.split(',') if request.user.volunteerprofile.interests else []
    user_interests = [interest.strip().lower() for interest in user_interests]
    
    context = {
        'categorized_events': categorized_events,
        'user_interests': user_interests,
        'tomorrow': tomorrow,
    }
    
    return render(request, 'core/volunteer_dashboard.html', context)

def manager_signup(request):
    if request.method == 'POST':
        form = EventManagerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('manager_dashboard')
    else:
        form = EventManagerSignupForm()
    return render(request, 'core/manager_signup.html', {'form': form})

def manager_login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('manager_dashboard')
    return render(request, 'core/manager_login.html')

@login_required
def manager_dashboard(request):
    manager_profile = get_object_or_404(EventManagerProfile, user=request.user)
    from datetime import date
    today = date.today()
    
    # Get upcoming and past events
    upcoming_events = Event.objects.filter(
        manager=manager_profile,
        date__gte=today
    ).order_by('date')
    
    past_events = Event.objects.filter(
        manager=manager_profile,
        date__lt=today
    ).order_by('-date')
    
    return render(request, 'core/manager_dashboard.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    })

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            manager_profile = get_object_or_404(EventManagerProfile, user=request.user)
            event.manager = manager_profile
            
            # Save latitude and longitude from form
            event.latitude = request.POST.get('latitude')
            event.longitude = request.POST.get('longitude')
            
            event.save()
            return redirect('manager_dashboard')
    else:
        form = EventForm()
    return render(request, 'core/create_event.html', {'form': form})

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated_event = form.save(commit=False)
            
            # Update latitude and longitude
            updated_event.latitude = request.POST.get('latitude')
            updated_event.longitude = request.POST.get('longitude')
            
            updated_event.save()
            return redirect('manager_dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'core/edit_event.html', {'form': form, 'event': event})

@login_required
def past_events(request):
    events = Event.objects.filter(date__lt='2024-01-01').order_by('-date')
    return render(request, 'core/past_events.html', {'events': events})

def user_logout(request):
    logout(request)
    return redirect('index')

def participate_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user.is_authenticated:
        if request.user in event.participation_requests.all():
            messages.info(request, "You have already requested to participate in this event.")
        elif request.user in event.participants.all():
            messages.info(request, "You are already a participant in this event.")
        else:
            event.participation_requests.add(request.user)
            messages.success(request, "Request sent to the event manager. Please wait for their response.")
    else:
        messages.error(request, "You need to log in to participate in events.")
    return redirect('volunteer_dashboard')

@login_required
def my_events(request):
    participated_events = request.user.participated_events.all()
    requested_events = request.user.requested_events.all()
    return render(request, 'core/my_events.html', {
        'participated_events': participated_events,
        'requested_events': requested_events,
    })

@login_required
def save_user_location(request):
    if request.method == 'POST':
        try:
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            # Update volunteer profile
            volunteer_profile = request.user.volunteerprofile
            volunteer_profile.latitude = latitude
            volunteer_profile.longitude = longitude
            volunteer_profile.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def manage_requests(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.manager.user != request.user:
        return redirect('manager_dashboard')  # Ensure only the event manager can access this page

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, id=user_id)

        if action == 'approve':
            event.participants.add(user)
            event.participation_requests.remove(user)
        elif action == 'reject':
            event.participation_requests.remove(user)

        return redirect('manage_requests', event_id=event.id)

    return render(request, 'core/manage_requests.html', {'event': event, 'requests': event.participation_requests.all()})

@login_required
def download_certificate(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user not in event.participants.all():
        messages.error(request, "You haven't participated in this event.")
        return redirect('my_events')
    
    # Certificate generation logic will be handled by frontend JavaScript
    return JsonResponse({
        'status': 'success',
        'event_name': event.name,
        'date': event.date.strftime('%B %d, %Y'),
        'volunteer_name': request.user.get_full_name() or request.user.username,
        'event_type': event.type
    })