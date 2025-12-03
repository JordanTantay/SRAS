from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ViolationViewSet
from .views import (
    login_view, logout_view, dashboard, monitor, violation_statistics, 
    violation_list, violation_detail, violation_image, delete_violation, 
    delete_multiple_violations, enforcer_list, add_enforcer, edit_enforcer, delete_enforcer,
    violation_plate_image, CurrentUserView, enforcer_profile, ViolationListView, 
    PendingViolationsView, pending_violation, approve_violation, cancel_violation, 
    pending_violation_image, api_violations_by_week, check_username_availability
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'api/violations', ViolationViewSet, basename='violation')

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('monitor/', monitor, name='monitor'),
    path('api/statistics/', violation_statistics, name='violation_statistics'), 
    path('violations/', violation_list, name='violation_list'),
    path('violations/<int:violation_id>/', violation_detail, name='violation_detail'),
    path('violations/<int:violation_id>/image/', violation_image, name='violation_image'),
    path('violations/<int:violation_id>/delete/', delete_violation, name='delete_violation'),
    path('violations/delete-multiple/', delete_multiple_violations, name='delete_multiple_violations'),
    path('violations/<int:pk>/plate.jpg', violation_plate_image, name='violation_plate_image'),

    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/me/', CurrentUserView.as_view(), name='current_user'),
    
    path('api/violations/pending/', PendingViolationsView.as_view(), name='pending_violations'),
    
    path('enforcers/', enforcer_list, name='enforcer_list'),
    path('enforcers/add/', add_enforcer, name='add_enforcer'),
    path('enforcers/<int:enforcer_id>/edit/', edit_enforcer, name='edit_enforcer'),
    path('enforcers/<int:enforcer_id>/delete/', delete_enforcer, name='delete_enforcer'),

    path('profile/', enforcer_profile, name='enforcer_profile'),
    path('pending_violation/', pending_violation, name='pending_violation'),
    path('violations/<int:violation_id>/approve/', approve_violation, name='approve_violation'),
    path('violations/<int:violation_id>/cancel/', cancel_violation, name='cancel_violation'),
    path('pending_violations/<int:violation_id>/image/', pending_violation_image, name='pending_violation_image'),
    
    path('api/violations_by_week/', api_violations_by_week, name='api_violations_by_week'),
    path('api/check-username/', check_username_availability, name='check_username'),
]

urlpatterns += router.urls
