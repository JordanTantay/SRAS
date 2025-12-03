from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse,Http404
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from .models import Violation, Enforcer, Camera, OriginalViolation
from rest_framework import serializers, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ViolationSerializer, ViolationVerificationSerializer, OriginalViolationSerializer
from rest_framework import viewsets, permissions
from rest_framework.decorators import action


class ViolationListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get query parameters for filtering
        status_filter = request.GET.get('status', None)
        
        violations = Violation.objects.select_related('camera').order_by('-timestamp')
        
        # Filter by status if provided
        if status_filter:
            violations = violations.filter(status=status_filter)
        
        serializer = ViolationSerializer(violations, many=True)
        return Response(serializer.data)

def login_view(request):
    """Login view that serves as the landing page"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('dashboard')
        return redirect('enforcer_profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                request.session['show_welcome_popup'] = True
                return redirect('dashboard')
            return redirect('enforcer_profile')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """Dashboard view - main admin interface"""
    import logging
    logger = logging.getLogger(__name__)

    # Get summary statistics from approved violations (timezone-aware, local day/week/month)
    import pytz
    local_tz = pytz.timezone('Asia/Manila')
    now = timezone.now().astimezone(local_tz)
    today_date = now.date()

    # Today
    start_today = local_tz.localize(datetime.combine(today_date, datetime.min.time()))
    end_today = local_tz.localize(datetime.combine(today_date, datetime.max.time()))
    start_today_utc = start_today.astimezone(pytz.UTC)
    end_today_utc = end_today.astimezone(pytz.UTC)
    logger.warning(f"[DEBUG] Dashboard Manila now: {now}, Today date: {today_date}")
    logger.warning(f"[DEBUG] Dashboard Start of today Manila: {start_today}, End of today Manila: {end_today}")
    logger.warning(f"[DEBUG] Dashboard Start of today UTC: {start_today_utc}, End of today UTC: {end_today_utc}")
    today_violations = OriginalViolation.objects.filter(timestamp__gte=start_today_utc, timestamp__lte=end_today_utc).count()

    # This week (Sunday to Saturday)
    week_start = today_date - timedelta(days=today_date.weekday() + 1 if today_date.weekday() != 6 else 0)
    week_end = week_start + timedelta(days=6)
    start_week = local_tz.localize(datetime.combine(week_start, datetime.min.time()))
    end_week = local_tz.localize(datetime.combine(week_end, datetime.max.time()))
    start_week_utc = start_week.astimezone(pytz.UTC)
    end_week_utc = end_week.astimezone(pytz.UTC)
    this_week_violations = OriginalViolation.objects.filter(timestamp__gte=start_week_utc, timestamp__lte=end_week_utc).count()

    # This month
    month_start = today_date.replace(day=1)
    last_day = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1))
    start_month = local_tz.localize(datetime.combine(month_start, datetime.min.time()))
    end_month = local_tz.localize(datetime.combine(last_day, datetime.max.time()))
    start_month_utc = start_month.astimezone(pytz.UTC)
    end_month_utc = end_month.astimezone(pytz.UTC)
    this_month_violations = OriginalViolation.objects.filter(timestamp__gte=start_month_utc, timestamp__lte=end_month_utc).count()

    total_violations = OriginalViolation.objects.count()

    # Get recent approved violations
    recent_violations = OriginalViolation.objects.all().order_by('-timestamp')[:5]

    # Get enforcer statistics
    total_enforcers = Enforcer.objects.count()
    active_enforcers = Enforcer.objects.filter(user__is_active=True).count()
    inactive_enforcers = total_enforcers - active_enforcers

    # Additional logging for debugging
    pending_count = Violation.objects.filter(status='pending_verification').count()
    logger.warning(f"[DASHBOARD] Approved violations: {total_violations}, Pending violations: {pending_count}")
    logger.warning(f"[DASHBOARD] Recent violations: {[v.id for v in recent_violations]}")

    show_welcome_popup = request.session.pop('show_welcome_popup', False)

    current_month_name = now.strftime("%B")
    context = {
        'total_violations': total_violations,
        'today_violations': today_violations,
        'this_week_violations': this_week_violations,
        'this_month_violations': this_month_violations,
        'recent_violations': recent_violations,
        'total_enforcers': total_enforcers,
        'active_enforcers': active_enforcers,
        'inactive_enforcers': inactive_enforcers,
        'show_welcome_popup': show_welcome_popup,
        'current_month_name': current_month_name,  # DEBUG: Added for card display
        'active_page': 'dashboard',
    }

    return render(request, 'core/dashboard.html', context)

@login_required
def enforcer_list(request):
    """View to display all enforcers"""
    enforcers = Enforcer.objects.all().order_by('user__username')
    cameras = Camera.objects.all()
    
    context = {
        'enforcers': enforcers,
        'cameras': cameras,
        'active_page': 'enforcer_list',
    }
    
    return render(request, 'core/enforcer_list.html', context)

@login_required
def add_enforcer(request):
    """View to add a new enforcer"""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email')
        password = request.POST.get('password')
        mobile_number = request.POST.get('mobile_number')
        assigned_camera_id = request.POST.get('assigned_camera')
        
        # Validation: Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'core/add_enforcer.html', {'cameras': Camera.objects.all()})
        
        # Validation: Check mobile number length (must be exactly 11 digits)
        if not mobile_number or len(mobile_number) != 11 or not mobile_number.isdigit():
            messages.error(request, 'Mobile number must be exactly 11 digits.')
            return render(request, 'core/add_enforcer.html', {'cameras': Camera.objects.all()})
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create enforcer
            enforcer = Enforcer.objects.create(
                user=user,
                mobile_number=mobile_number,
                assigned_camera_id=assigned_camera_id if assigned_camera_id else None
            )
            
            full_name = f"{first_name} {last_name}".strip() or username
            messages.success(request, f'Enforcer "{full_name}" has been created successfully.')
            return redirect('enforcer_list')
            
        except Exception as e:
            messages.error(request, f'Error creating enforcer: {str(e)}')
            return render(request, 'core/add_enforcer.html', {'cameras': Camera.objects.all()})
    
    context = {
        'cameras': Camera.objects.all(),
    }
    
    return render(request, 'core/add_enforcer.html', context)

@login_required
def edit_enforcer(request, enforcer_id):
    """View to edit an existing enforcer"""
    enforcer = get_object_or_404(Enforcer, id=enforcer_id)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email')
        mobile_number = request.POST.get('mobile_number')
        assigned_camera_id = request.POST.get('assigned_camera')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Update user
            enforcer.user.first_name = first_name
            enforcer.user.last_name = last_name
            enforcer.user.email = email
            enforcer.user.is_active = is_active
            enforcer.user.save()
            
            # Update enforcer
            enforcer.mobile_number = mobile_number
            enforcer.assigned_camera_id = assigned_camera_id if assigned_camera_id else None
            enforcer.save()
            
            return redirect('enforcer_list')
            
        except Exception as e:
            messages.error(request, f'Error updating enforcer: {str(e)}')
    
    context = {
        'enforcer': enforcer,
        'cameras': Camera.objects.all(),
    }
    
    return render(request, 'core/edit_enforcer.html', context)

@login_required
def delete_enforcer(request, enforcer_id):
    """Delete an enforcer"""
    if request.method == 'POST':
        try:
            enforcer = get_object_or_404(Enforcer, id=enforcer_id)
            username = enforcer.user.username
            enforcer.user.delete()  # This will also delete the enforcer due to CASCADE
            messages.success(request, f'Enforcer "{username}" has been deleted successfully.')
            return redirect('enforcer_list')
        except Exception as e:
            messages.error(request, f'Error deleting enforcer: {str(e)}')
            return redirect('enforcer_list')
    else:
        return redirect('enforcer_list')

@login_required
def monitor(request):
    """Main monitoring page - points to stream_mjpeg.py server"""
    return render(request, "core/monitor.html", {'active_page': 'monitor'})

def violation_statistics(request):
    """API endpoint to get violation statistics for the last 5 days and current week (Sun-Sat)"""
    import logging
    logger = logging.getLogger(__name__)
    import pytz

    # Get the last 5 days (including today)
    local_tz = pytz.timezone('Asia/Manila')
    manila_now = timezone.now().astimezone(local_tz)
    end_date = manila_now.date()
    start_date = end_date - timedelta(days=4)

    # Create a list of dates for the last 5 days
    dates = []
    for i in range(5):
        date = end_date - timedelta(days=4-i)
        dates.append(date)

    # Get approved violation counts for each date
    local_tz = pytz.timezone('Asia/Manila')
    statistics = []
    for date in dates:
        start_dt = local_tz.localize(datetime.combine(date, datetime.min.time()))
        end_dt = local_tz.localize(datetime.combine(date, datetime.max.time()))
        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)
        qs = OriginalViolation.objects.filter(timestamp__gte=start_utc, timestamp__lte=end_utc)
        count = qs.count()
        logger.warning(f"[STATISTICS] Date: {date}, Range: {start_utc} to {end_utc}, Count: {count}, IDs: {[v.id for v in qs]}")
        statistics.append({
            'date': date.strftime('%Y-%m-%d'),
            'display_date': date.strftime('%d %b'),  # Format as "01 May"
            'count': count
        })

    # Get current week (Sunday to Saturday)
    today = timezone.now().date()
    # Find the most recent Sunday
    week_start = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    week_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    week_statistics = []
    for i, date in enumerate(week_dates):
        start_dt = local_tz.localize(datetime.combine(date, datetime.min.time()))
        end_dt = local_tz.localize(datetime.combine(date, datetime.max.time()))
        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)
        qs = OriginalViolation.objects.filter(timestamp__gte=start_utc, timestamp__lte=end_utc)
        count = qs.count()
        logger.warning(f"[WEEK_STATS] {week_labels[i]} {date}: {count}")
        week_statistics.append({
            'label': week_labels[i],
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })

    # Calculate statistics for each week of the current month (real calendar weeks, Sun-Sat)
    import calendar
    month_statistics = []
    first_day = today.replace(day=1)
    last_day = (first_day.replace(month=first_day.month % 12 + 1, day=1) - timedelta(days=1))
    # Use the real first day of the month, not the first Sunday
    week_ranges = []
    current = first_day
    month_statistics = []
    month_weekly_daily = []  # For each week: { label, days: [ {label, count}, ... ] }
    # Use real calendar month for monthly violation tracking
    # Start = first day of month, End = last day of month
    total_days_in_month = (last_day - first_day).days + 1
    month_days = []
    for i in range(total_days_in_month):
        day = first_day + timedelta(days=i)
        start_dt = local_tz.localize(datetime.combine(day, datetime.min.time()))
        end_dt = local_tz.localize(datetime.combine(day, datetime.max.time()))
        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)
        qs = OriginalViolation.objects.filter(timestamp__gte=start_utc, timestamp__lte=end_utc)
        count = qs.count()
        month_days.append({
            'label': day.strftime('%a'),
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    logger.warning(f"[MONTH_STATS] Real calendar month days: {month_days}")

    # Optionally, group by week for display (Sun-Sat)
    month_weekly_daily = []
    # Group days into 4 weeks, add any remaining days to week 4
    week_start_idx = 0
    for week_num in range(4):
        start = week_start_idx
        end = min(week_start_idx + 7, len(month_days))
        week_days = month_days[start:end]
        # For week 4, add all remaining days
        if week_num == 3 and end < len(month_days):
            week_days += month_days[end:]
            end = len(month_days)
        month_weekly_daily.append({
            'label': f'Week {week_num+1}',
            'days': week_days
        })
        week_start_idx = end

    # --- DEBUG LOGS for month week/day coverage ---
    days_covered = 0
    for week in month_weekly_daily:
        days_covered += len(week['days'])
    total_days_in_month = (last_day - first_day).days + 1
    remaining_days = total_days_in_month - days_covered
    logger.warning(f"[MONTH_STATS] Days covered by first 4 weeks: {days_covered}, Total days in month: {total_days_in_month}, Remaining days: {remaining_days}")

    # Add remaining days after 4 weeks
    extra_days = []
    if remaining_days > 0:
        # Determine month type
        if total_days_in_month == 30:
            extra_count = 2
        elif total_days_in_month == 31:
            extra_count = 3
        elif total_days_in_month == 28:
            extra_count = 0
        elif total_days_in_month == 29:
            extra_count = 1
        else:
            extra_count = remaining_days  # fallback
        # Get the actual dates for the extra days
        for i in range(extra_count):
            day = last_day - timedelta(days=extra_count - i - 1)
            start_dt = local_tz.localize(datetime.combine(day, datetime.min.time()))
            end_dt = local_tz.localize(datetime.combine(day, datetime.max.time()))
            start_utc = start_dt.astimezone(pytz.UTC)
            end_utc = end_dt.astimezone(pytz.UTC)
            qs = OriginalViolation.objects.filter(timestamp__gte=start_utc, timestamp__lte=end_utc)
            count = qs.count()
            extra_days.append({
                'label': day.strftime('%a'),
                'date': day.strftime('%Y-%m-%d'),
                'count': count
            })
        logger.warning(f"[MONTH_STATS] Extra days added: {extra_days}")

        # Optionally, append to month_weekly_daily for display
        month_weekly_daily.append({
            'label': 'Remaining Days',
            'days': extra_days
        })

    # Calculate statistics for each hour of today (local time)
    today_hourly = []
    for hour in range(24):
        hour_start = local_tz.localize(datetime.combine(today, datetime.min.time()) + timedelta(hours=hour))
        hour_end = hour_start + timedelta(minutes=59, seconds=59, microseconds=999999)
        hour_start_utc = hour_start.astimezone(pytz.UTC)
        hour_end_utc = hour_end.astimezone(pytz.UTC)
        qs = OriginalViolation.objects.filter(timestamp__gte=hour_start_utc, timestamp__lte=hour_end_utc)
        count = qs.count()
        logger.warning(f"[TODAY_HOURLY] {hour:02d}:00 - {hour:02d}:59: {count}")
        today_hourly.append({
            'hour': f"{hour:02d}:00",
            'count': count
        })

    logger.warning(f"[STATISTICS] Final statistics: {statistics}")
    logger.warning(f"[WEEK_STATS] {week_statistics}")
    logger.warning(f"[MONTH_STATS] {month_statistics}")
    logger.warning(f"[MONTH_WEEKLY_DAILY] {month_weekly_daily}")
    logger.warning(f"[TODAY_HOURLY] {today_hourly}")
    return JsonResponse({
        'statistics': statistics,
        'total_violations': sum(item['count'] for item in statistics),
        'week_statistics': week_statistics,
        'month_statistics': month_statistics,
        'month_weekly_daily': month_weekly_daily,
        'today_hourly': today_hourly
    })

# --- API for dashboard week filter ---
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_violations_by_week(request):
    """
    API endpoint to get violations for a given week (Sun-Sat).
    Accepts GET params: start_date, end_date (YYYY-MM-DD).
    Returns: list of violations (id, plate_number, camera name, timestamp).
    """
    import pytz
    from django.utils.dateparse import parse_date
    import logging
    logger = logging.getLogger(__name__)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if not start_date or not end_date:
        return JsonResponse({'error': 'start_date and end_date required'}, status=400)

    try:
        local_tz = pytz.timezone('Asia/Manila')
        start_dt = local_tz.localize(datetime.combine(parse_date(start_date), datetime.min.time()))
        end_dt = local_tz.localize(datetime.combine(parse_date(end_date), datetime.max.time()))
        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)
    except Exception as e:
        logger.error(f"Invalid date params: {e}")
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    violations = OriginalViolation.objects.filter(timestamp__gte=start_utc, timestamp__lte=end_utc).select_related('camera').order_by('-timestamp')
    logger.warning(f"[API_WEEK] {start_date} to {end_date}: {violations.count()} violations")
    data = [
        {
            'id': v.id,
            'plate_number': v.plate_number,
            'camera': v.camera.name if v.camera else "Unknown Camera",
            'timestamp': v.timestamp.astimezone(local_tz).strftime('%b %d, %Y %H:%M')
        }
        for v in violations
    ]
    return JsonResponse({'violations': data})
    logger.warning(f"[API_WEEK] Returned {len(data)} violations for {start_date} to {end_date}")

@login_required
def violation_list(request):
    """View to display all approved violations from OriginalViolation database"""
    # Get search parameters
    search = request.GET.get('search', '')
    date_filter = request.GET.get('date', '')
    plate_filter = request.GET.get('plate', '')
    
    # Get all approved violations ordered by timestamp (newest first)
    violations = OriginalViolation.objects.all().order_by('-timestamp')
    
    # Apply filters
    import logging
    logger = logging.getLogger(__name__)

    if search:
        violations = violations.filter(
            Q(plate_number__icontains=search) |
            Q(camera__name__icontains=search)
        )
        logger.warning(f"Search filter applied: '{search}', count: {violations.count()}")

    if date_filter:
        try:
            # Parse month/year format (YYYY-MM)
            filter_date = datetime.strptime(date_filter, '%Y-%m')
            import pytz
            import calendar
            local_tz = pytz.timezone('Asia/Manila')
            
            # Get first day of the month
            first_day = filter_date.replace(day=1)
            # Get last day of the month
            last_day_num = calendar.monthrange(filter_date.year, filter_date.month)[1]
            last_day = filter_date.replace(day=last_day_num)
            
            # Create datetime range for the entire month
            start_dt = local_tz.localize(datetime.combine(first_day.date(), datetime.min.time()))
            end_dt = local_tz.localize(datetime.combine(last_day.date(), datetime.max.time()))
            start_utc = start_dt.astimezone(pytz.UTC)
            end_utc = end_dt.astimezone(pytz.UTC)
            
            violations = violations.filter(timestamp__gte=start_utc, timestamp__lte=end_utc)
            logger.warning(f"Month filter applied: {date_filter} ({start_utc} to {end_utc}), count: {violations.count()}")
        except ValueError:
            logger.error(f"Invalid date_filter format: {date_filter}")

    if plate_filter:
        violations = violations.filter(plate_number__icontains=plate_filter)
        logger.warning(f"Plate filter applied: '{plate_filter}', count: {violations.count()}")
    
    # Pagination
    paginator = Paginator(violations, 20)  # Show 20 violations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_violations = violations.count()

    # --- LOGGING FOR DIAGNOSIS ---
    import pytz
    local_tz = pytz.timezone('Asia/Manila')
    manila_now = timezone.now().astimezone(local_tz)
    today_date = manila_now.date()
    start_today = local_tz.localize(datetime.combine(today_date, datetime.min.time()))
    end_today = local_tz.localize(datetime.combine(today_date, datetime.max.time()))
    start_today_utc = start_today.astimezone(pytz.UTC)
    end_today_utc = end_today.astimezone(pytz.UTC)
    logger.warning(f"[DEBUG] Manila now: {manila_now}, Today date: {today_date}")
    logger.warning(f"[DEBUG] Start of today Manila: {start_today}, End of today Manila: {end_today}")
    logger.warning(f"[DEBUG] Start of today UTC: {start_today_utc}, End of today UTC: {end_today_utc}")
    today_violations = OriginalViolation.objects.filter(timestamp__gte=start_today_utc, timestamp__lte=end_today_utc).count()
    logger.warning(f"[VIOLATION_LIST] Asia/Manila today: {today_date}, UTC now: {timezone.now()}, Today violations: {today_violations}")
    this_week_violations = violations.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_violations': total_violations,
        'today_violations': today_violations,
        'this_week_violations': this_week_violations,
        'search': search,
        'date_filter': date_filter,
        'plate_filter': plate_filter,
        'active_page': 'violation_list',
    }
    
    return render(request, "core/violation_list.html", context)

@login_required
def pending_violation_image(request, violation_id):
    """View to display violation image from Violation (pending) database"""
    try:
        violation = Violation.objects.get(id=violation_id)
        return HttpResponse(violation.image, content_type='image/jpeg')
    except Violation.DoesNotExist:
        return HttpResponse("Image not found", status=404)

@login_required
def violation_image(request, violation_id):
    """View to display violation image from OriginalViolation database"""
    try:
        violation = OriginalViolation.objects.get(id=violation_id)
        # Return the image as HTTP response
        return HttpResponse(violation.image, content_type='image/jpeg')
    except OriginalViolation.DoesNotExist:
        return HttpResponse("Image not found", status=404)

@never_cache
def violation_plate_image(request, pk: int):
    v = get_object_or_404(OriginalViolation, pk=pk)
    data = v.plate_image
    if not data:
        raise Http404("Plate image not available")

    # BinaryField often returns a memoryview; normalize to raw bytes.
    if isinstance(data, memoryview):
        data = data.tobytes()
    elif isinstance(data, bytearray):
        data = bytes(data)

    # Optionally validate JPEG SOI marker to avoid blank renders
    if not (len(data) > 2 and data[0] == 0xFF and data[1] == 0xD8):
        # Not a JPEG; the stored bytes are likely wrong
        raise Http404("Invalid plate image bytes")

    resp = HttpResponse(data, content_type="image/jpeg")
    resp["Cache-Control"] = "no-store"
    return resp

@login_required
def violation_detail(request, violation_id):
    """View to show detailed information about a specific approved violation"""
    try:
        violation = OriginalViolation.objects.get(id=violation_id)
        context = {
            'violation': violation,
        }
        return render(request, "core/violation_detail.html", context)
    except OriginalViolation.DoesNotExist:
        return HttpResponse("Violation not found", status=404)

@login_required
def delete_violation(request, violation_id):
    """Delete a specific approved violation"""
    if request.method == 'POST':
        try:
            violation = get_object_or_404(OriginalViolation, id=violation_id)
            violation_id = violation.id
            violation.delete()
            messages.success(request, f'Violation #{violation_id} has been deleted successfully.')
            return redirect('violation_list')
        except Exception as e:
            messages.error(request, f'Error deleting violation: {str(e)}')
            return redirect('violation_list')
    else:
        # If not POST request, redirect to violation list
        return redirect('violation_list')

@login_required
def delete_multiple_violations(request):
    """Delete multiple violations at once"""
    if request.method == 'POST':
        violation_ids = request.POST.getlist('violation_ids')
        deleted_count = 0
        
        for violation_id in violation_ids:
            try:
                violation = OriginalViolation.objects.get(id=violation_id)
                violation.delete()
                deleted_count += 1
            except OriginalViolation.DoesNotExist:
                continue
        
        if deleted_count > 0:
            messages.success(request, f'{deleted_count} violation(s) have been deleted successfully.')
        else:
            messages.warning(request, 'No violations were deleted.')
        
        return redirect('violation_list')
    else:
        return redirect('violation_list')


class CurrentUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]

    def get_full_name(self, obj):
        full_name = (obj.first_name or "").strip() + " " + (obj.last_name or "").strip()
        return full_name.strip() or obj.username

    def get_role(self, obj):
        if obj.is_superuser:
            return "admin"
        return "user"


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = CurrentUserSerializer(request.user).data
        return Response(data)


@login_required
def enforcer_profile(request):
    """Profile page for non-admin users to view personal info"""
    enforcer = None
    try:
        enforcer = Enforcer.objects.select_related('user', 'assigned_camera').get(user=request.user)
    except Enforcer.DoesNotExist:
        enforcer = None

    context = {
        'user_obj': request.user,
        'enforcer': enforcer,
    }
    return render(request, 'core/enforcer_profile.html', context)

class ViolationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Violation.objects.all().order_by('-timestamp')
    serializer_class = ViolationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def image(self, request, pk=None):
        violation = self.get_object()
        return HttpResponse(violation.image, content_type='image/jpeg')

    @action(detail=True, methods=['patch'])
    def verify(self, request, pk=None):
        """Verify a violation (approve or reject)"""
        import logging
        logger = logging.getLogger(__name__)
        
        violation = self.get_object()
        logger.warning(f"[VERIFY] Violation {pk} current status: {violation.status}")
        
        # Check if violation is still pending
        if violation.status != 'pending_verification':
            return Response(
                {'error': 'Violation has already been verified'}, 
                status=400
            )
        
        serializer = ViolationVerificationSerializer(violation, data=request.data, partial=True)
        if serializer.is_valid():
            # Update verification details
            violation.verified_by = request.user
            violation.verified_at = timezone.now()
            violation.status = serializer.validated_data['status']
            violation.verification_notes = serializer.validated_data.get('verification_notes', '')
            violation.save()
            
            logger.warning(f"[VERIFY] Violation {pk} updated to status: {violation.status}")
            
            # If approved, create an OriginalViolation record
            if violation.status == 'approved':
                original_violation = OriginalViolation.objects.create(
                    camera=violation.camera,
                    timestamp=violation.timestamp,
                    plate_number=violation.plate_number,
                    image=violation.image,
                    plate_image=violation.plate_image,
                    verified_by=violation.verified_by,
                    verified_at=violation.verified_at,
                    verification_notes=violation.verification_notes,
                    original_violation=violation,
                    sms_sent=violation.sms_sent,
                    rider_hash=violation.rider_hash
                )
                logger.warning(f"[VERIFY] Created OriginalViolation {original_violation.id} for Violation {pk}")
            
            return Response({
                'message': f'Violation {violation.status} successfully',
                'violation': ViolationSerializer(violation).data
            })
        
        return Response(serializer.errors, status=400)

@login_required
def approve_violation(request, violation_id):
    """Approve a pending violation and move to violation list"""
    violation = get_object_or_404(Violation, id=violation_id, status='pending_verification')
    if request.method == 'POST':
        violation.status = 'approved'
        violation.verified_by = request.user
        violation.verified_at = timezone.now()
        violation.save()
        # Create OriginalViolation record preserving the original capture timestamp
        OriginalViolation.objects.create(
            camera=violation.camera,
            timestamp=violation.timestamp,  # Use original capture time, not current time
            plate_number=violation.plate_number,
            image=violation.image,
            plate_image=violation.plate_image,
            verified_by=violation.verified_by,
            verified_at=violation.verified_at,
            verification_notes=violation.verification_notes,
            original_violation=violation,
            sms_sent=violation.sms_sent,
            rider_hash=violation.rider_hash
        )
        # Store message in session for pending_violation page only
        request.session['pending_violation_message'] = {
            'type': 'success',
            'text': f'Violation #{violation.id} approved successfully.'
        }
    return redirect('pending_violation')

@login_required
def cancel_violation(request, violation_id):
    """Cancel a pending violation"""
    violation = get_object_or_404(Violation, id=violation_id, status='pending_verification')
    if request.method == 'POST':
        violation.status = 'cancelled'
        violation.verified_by = request.user
        violation.verified_at = timezone.now()
        violation.save()
        # Store message in session for pending_violation page only
        request.session['pending_violation_message'] = {
            'type': 'info',
            'text': f'Violation #{violation.id} cancelled successfully.'
        }
    return redirect('pending_violation')

@login_required
def pending_violation(request):
    """Page to list all pending violations for admin review"""
    pending_violations = Violation.objects.filter(status='pending_verification').select_related('camera').order_by('-timestamp')
    
    # Get and clear the session message if it exists
    message = request.session.pop('pending_violation_message', None)
    
    context = {
        'pending_violations': pending_violations,
        'active_page': 'pending_violation',
        'flash_message': message,
    }
    return render(request, 'core/pending_violation.html', context)

class PendingViolationsView(APIView):
    """API endpoint to get only pending violations for verification"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        pending_violations = Violation.objects.filter(
            status='pending_verification'
        ).select_related('camera').order_by('-timestamp')
        
        serializer = ViolationSerializer(pending_violations, many=True)
        return Response(serializer.data)

def check_username_availability(request):
    """API endpoint to check if a username is available"""
    username = request.GET.get('username', '').strip()
    
    if not username:
        return JsonResponse({'exists': False, 'message': 'Username is required'})
    
    exists = User.objects.filter(username=username).exists()
    
    return JsonResponse({
        'exists': exists,
        'username': username,
        'message': 'Username already exists' if exists else 'Username available'
    })
