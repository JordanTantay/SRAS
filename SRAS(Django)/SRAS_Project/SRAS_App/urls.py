from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ViolationViewSet
from .views import (
    login_view, logout_view, dashboard, monitor, violation_statistics, 
    violation_list, violation_detail, violation_image, delete_violation, 
    delete_multiple_violations, enforcer_list, add_enforcer, edit_enforcer, delete_enforcer,violation_plate_image,                                              
    CurrentUserView, enforcer_profile,ViolationListView, PendingViolationsView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
router = DefaultRouter()
router.register(r'api/violations', ViolationViewSet)

urlpatterns = [
    path('', login_view, name='login'),  # Landing page
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

    # Auth API (JWT) and current user
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),                                                                           
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),                                                                          
    path('api/users/me/', CurrentUserView.as_view(), name='current_user'),
    
    # New verification endpoints
    path('api/violations/pending/', PendingViolationsView.as_view(), name='pending_violations'),
    
    path('enforcers/', enforcer_list, name='enforcer_list'),
    path('enforcers/add/', add_enforcer, name='add_enforcer'),
    path('enforcers/<int:enforcer_id>/edit/', edit_enforcer, name='edit_enforcer'),                                                                             
    path('enforcers/<int:enforcer_id>/delete/', delete_enforcer, name='delete_enforcer'),                                                                       

    # Enforcer/user profile
    path('profile/', enforcer_profile, name='enforcer_profile'),
]+ router.urls