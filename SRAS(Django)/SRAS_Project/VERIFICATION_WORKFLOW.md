# Violation Verification Workflow

This document describes the new violation verification workflow implemented in the SRAS system.

## Overview

The system now supports a two-stage verification process:
1. **Detection**: Violations are detected by the Django admin system and marked as `pending_verification`
2. **Verification**: Android app users can review and approve/reject violations

## Workflow Steps

### 1. Violation Detection (Django Admin)
- When a violation is detected, it's automatically saved with `status = 'pending_verification'`
- The violation is stored in the database but not yet considered "official"

### 2. User Verification (Android App)
- Android app users can view pending violations in the "Pending Verifications" section
- Each violation shows:
  - Violation image
  - Plate number
  - Camera name
  - Timestamp
- Users can either:
  - **Approve**: Violation becomes official (`status = 'approved'`)
  - **Reject**: Violation is marked as invalid (`status = 'rejected'`)

### 3. Database Update
- Approved violations remain in the database and can be used for enforcement
- Rejected violations are marked but kept for audit purposes

## API Endpoints

### Django Backend

#### Get Pending Violations
```
GET /api/violations/pending/
Authorization: Bearer <token>
```
Returns all violations with `status = 'pending_verification'`

#### Verify Violation
```
PATCH /api/violations/{id}/verify/
Authorization: Bearer <token>
Content-Type: application/json

{
    "status": "approved" | "rejected",
    "verification_notes": "Optional notes"
}
```

#### Get All Violations (with filtering)
```
GET /api/violations/?status=pending_verification
Authorization: Bearer <token>
```

### Android App

#### New Activities
- `MainActivity`: Dashboard with options to view all violations or pending verifications
- `PendingVerificationActivity`: Shows list of violations awaiting verification
- `VerificationDialog`: Dialog for approving/rejecting individual violations

#### New Models
- Updated `Violation` model with verification fields
- `ViolationVerification` model for API requests

## Database Schema Changes

### Violation Model Updates
```python
class Violation(models.Model):
    # ... existing fields ...
    
    # New verification fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
```

### Status Choices
- `pending_verification`: Awaiting user verification (default)
- `approved`: Verified and approved by user
- `rejected`: Verified and rejected by user

## Testing

### Create Test Data
```bash
# Run Django server
python manage.py runserver

# Create test violations (optional)
python manage.py create_test_pending_violations

# Test API endpoints
python test_verification_api.py
```

### Android Testing
1. Build and install the Android app
2. Login with valid credentials
3. Navigate to "Pending Verifications"
4. Test approve/reject functionality

## Configuration

### Django Settings
Ensure the following are configured:
- CORS headers for Android app communication
- JWT authentication
- Database migrations applied

### Android Configuration
Update the base URL in `ApiService.kt`:
```kotlin
.baseUrl("http://YOUR_DJANGO_SERVER_IP:8000/")
```

## Security Considerations

1. **Authentication**: All API endpoints require valid JWT tokens
2. **Authorization**: Users can only verify violations they have access to
3. **Audit Trail**: All verification actions are logged with user and timestamp
4. **Data Integrity**: Rejected violations are preserved for audit purposes

## Future Enhancements

1. **Push Notifications**: Notify users when new violations need verification
2. **Batch Verification**: Allow multiple violations to be verified at once
3. **Verification History**: Show history of verification actions
4. **Advanced Filtering**: Filter violations by camera, time range, etc.
5. **Statistics**: Track verification metrics and user performance

## Troubleshooting

### Common Issues

1. **No Pending Violations**: Ensure violations are created with `status='pending_verification'`
2. **API Connection Failed**: Check Django server is running and accessible from Android device
3. **Authentication Failed**: Verify JWT tokens are valid and not expired
4. **Image Loading Issues**: Ensure image URLs are accessible from Android device

### Debug Steps

1. Check Django logs for API errors
2. Use Android Studio logcat to debug app issues
3. Test API endpoints using curl or Postman
4. Verify database has test data with correct status
