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
            messages.success(request, f'Welcome back, {user.username}!')
            if user.is_superuser:
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
    # Get summary statistics from approved violations
    total_violations = OriginalViolation.objects.count()
    today_violations = OriginalViolation.objects.filter(timestamp__date=timezone.now().date()).count()
    this_week_violations = OriginalViolation.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).count()
    this_month_violations = OriginalViolation.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Get recent approved violations
    recent_violations = OriginalViolation.objects.all().order_by('-timestamp')[:5]
    
    # Get enforcer statistics
    total_enforcers = Enforcer.objects.count()
    active_enforcers = Enforcer.objects.filter(user__is_active=True).count()
    
    context = {
        'total_violations': total_violations,
        'today_violations': today_violations,
        'this_week_violations': this_week_violations,
        'this_month_violations': this_month_violations,
        'recent_violations': recent_violations,
        'total_enforcers': total_enforcers,
        'active_enforcers': active_enforcers,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def enforcer_list(request):
    """View to display all enforcers"""
    enforcers = Enforcer.objects.all().order_by('user__username')
    
    context = {
        'enforcers': enforcers,
    }
    
    return render(request, 'core/enforcer_list.html', context)

@login_required
def add_enforcer(request):
    """View to add a new enforcer"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        mobile_number = request.POST.get('mobile_number')
        assigned_camera_id = request.POST.get('assigned_camera')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'core/add_enforcer.html', {'cameras': Camera.objects.all()})
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create enforcer
            enforcer = Enforcer.objects.create(
                user=user,
                mobile_number=mobile_number,
                assigned_camera_id=assigned_camera_id if assigned_camera_id else None
            )
            
            messages.success(request, f'Enforcer "{username}" has been created successfully.')
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
        email = request.POST.get('email')
        mobile_number = request.POST.get('mobile_number')
        assigned_camera_id = request.POST.get('assigned_camera')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Update user
            enforcer.user.email = email
            enforcer.user.is_active = is_active
            enforcer.user.save()
            
            # Update enforcer
            enforcer.mobile_number = mobile_number
            enforcer.assigned_camera_id = assigned_camera_id if assigned_camera_id else None
            enforcer.save()
            
            messages.success(request, f'Enforcer "{enforcer.user.username}" has been updated successfully.')
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
    return render(request, "core/monitor.html")

def violation_statistics(request):
    """API endpoint to get violation statistics for the last 5 days"""
    # Get the last 5 days (including today)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=4)
    
    # Create a list of dates for the last 5 days
    dates = []
    for i in range(5):
        date = end_date - timedelta(days=4-i)
        dates.append(date)
    
    # Get approved violation counts for each date
    statistics = []
    for date in dates:
        count = OriginalViolation.objects.filter(
            timestamp__date=date
        ).count()
        statistics.append({
            'date': date.strftime('%Y-%m-%d'),
            'display_date': date.strftime('%d %b'),  # Format as "01 May"
            'count': count
        })
    
    return JsonResponse({
        'statistics': statistics,
        'total_violations': sum(item['count'] for item in statistics)
    })

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
    if search:
        violations = violations.filter(
            Q(plate_number__icontains=search) |
            Q(camera__name__icontains=search)
        )
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            violations = violations.filter(timestamp__date=filter_date)
        except ValueError:
            pass
    
    if plate_filter:
        violations = violations.filter(plate_number__icontains=plate_filter)
    
    # Pagination
    paginator = Paginator(violations, 20)  # Show 20 violations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_violations = violations.count()
    today_violations = violations.filter(timestamp__date=timezone.now().date()).count()
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
    }
    
    return render(request, "core/violation_list.html", context)

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
        violation = self.get_object()
        
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
            
            # If approved, create an OriginalViolation record
            if violation.status == 'approved':
                original_violation = OriginalViolation.objects.create(
                    camera=violation.camera,
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
            
            return Response({
                'message': f'Violation {violation.status} successfully',
                'violation': ViolationSerializer(violation).data
            })
        
        return Response(serializer.errors, status=400)

class PendingViolationsView(APIView):
    """API endpoint to get only pending violations for verification"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        pending_violations = Violation.objects.filter(
            status='pending_verification'
        ).select_related('camera').order_by('-timestamp')
        
        serializer = ViolationSerializer(pending_violations, many=True)
        return Response(serializer.data)
