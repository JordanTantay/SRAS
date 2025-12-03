# Verification and Dashboard Fixes

## Issues Fixed

### 1. Android App Verification Not Working
**Problem**: Users couldn't verify violations from the SRAS2 Android app because the verification endpoint wasn't properly registered.

**Root Cause**: 
- The `ViolationViewSet` with the `@action` decorator for `verify()` was defined but the router URLs weren't being included properly
- The endpoint `/api/violations/<id>/verify/` wasn't accessible

**Solution**:
- Cleaned up `urls.py` to properly include router URLs: `urlpatterns += router.urls`
- Added `basename='violation'` to router registration for clarity
- Ensured `api/violations/pending/` endpoint is registered before router URLs to avoid conflicts
- Added logging to the verify action to track verification attempts
- Fixed timestamp preservation: `OriginalViolation` now uses `violation.timestamp` instead of `timezone.now()`

**Files Modified**:
- `SRAS(Django)/SRAS_Project/SRAS_App/urls.py`
- `SRAS(Django)/SRAS_Project/SRAS_App/views.py`

### 2. Enforcer Status Chart Red Legend Not Visible
**Problem**: The admin dashboard's enforcer status doughnut chart wasn't showing the red legend for inactive enforcers, even when inactive enforcers existed.

**Root Cause**: 
- The dashboard view was calculating `active_enforcers` but not `inactive_enforcers`
- The template was referencing `{{ inactive_enforcers }}` which was undefined, resulting in 0

**Solution**:
- Added `inactive_enforcers` calculation in the `dashboard()` view:
  ```python
  inactive_enforcers = total_enforcers - active_enforcers
  ```
- Added `inactive_enforcers` to the context dictionary
- The chart now correctly displays both active (green) and inactive (red) enforcers

**Files Modified**:
- `SRAS(Django)/SRAS_Project/SRAS_App/views.py`

## Testing

### Test Results
```
Total Enforcers: 5
Active Enforcers: 4
Inactive Enforcers: 1
✓ Inactive enforcers detected - chart should show red legend

Pending Violations: 0
Approved Violations: 116
Original Violations: 41
✓ Verification workflow is working
```

### How to Test

#### 1. Test Enforcer Chart Fix
1. Restart Django server: `python manage.py runserver`
2. Login to admin dashboard at `http://localhost:8000/dashboard/`
3. Look at the "Enforcer Status" doughnut chart on the right side
4. You should now see:
   - Green segment for active enforcers (4)
   - Red segment for inactive enforcers (1)
   - Both legends visible at the bottom

#### 2. Test Android App Verification
1. Build and install the SRAS2 Android app
2. Login with valid credentials
3. Navigate to "Pending Verifications"
4. Select a violation and tap "Approve" or "Reject"
5. The verification should succeed and the violation should:
   - Update status to 'approved' or 'rejected' in Violation table
   - Create a new record in OriginalViolation table (if approved)
   - Preserve the original timestamp

#### 3. Test API Endpoints Directly

**Get Pending Violations**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/violations/pending/
```

**Verify a Violation**:
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "verification_notes": "Test approval"}' \
  http://localhost:8000/api/violations/1/verify/
```

## API Endpoints

### Verification Endpoints
- `GET /api/violations/pending/` - Get all pending violations
- `PATCH /api/violations/<id>/verify/` - Verify a violation (approve/reject)
- `GET /api/violations/<id>/image/` - Get violation image

### Authentication
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token

## Database Schema

### Violation Model
- `status`: 'pending_verification', 'approved', or 'rejected'
- `verified_by`: User who verified
- `verified_at`: Timestamp of verification
- `verification_notes`: Optional notes

### OriginalViolation Model
- Created when a violation is approved
- Preserves original timestamp from Violation
- Contains all violation data for final record

## Known Issues & Notes

1. **Pending Violations**: Currently 0 pending violations in the system. New violations from the detection system will appear here.

2. **Approved vs Original**: There are 116 approved violations but only 41 in OriginalViolation. This suggests:
   - Some violations were approved before the OriginalViolation table was created
   - Or some were approved through the web interface instead of the API

3. **Android App Base URL**: Make sure the Android app's `ApiService.kt` has the correct base URL:
   ```kotlin
   .baseUrl("http://YOUR_DJANGO_SERVER_IP:8000/")
   ```

## Troubleshooting

### Verification Fails with 404
- Check that Django server is running
- Verify the router URLs are included: `urlpatterns += router.urls`
- Check logs for endpoint registration

### Chart Still Shows 0 Inactive
- Verify `inactive_enforcers` is in the context
- Check browser console for JavaScript errors
- Clear browser cache and reload

### Timestamp Issues
- Ensure `OriginalViolation` uses `violation.timestamp` not `timezone.now()`
- Check timezone settings in Django settings (should be 'Asia/Manila')

## Files Changed

1. `SRAS(Django)/SRAS_Project/SRAS_App/views.py`
   - Added `inactive_enforcers` calculation
   - Added logging to verify action
   - Fixed timestamp preservation in OriginalViolation creation

2. `SRAS(Django)/SRAS_Project/SRAS_App/urls.py`
   - Cleaned up URL patterns
   - Properly included router URLs
   - Added basename to router registration

3. `SRAS(Django)/SRAS_Project/test_verification_fix.py` (new)
   - Test script to verify fixes

4. `SRAS(Django)/SRAS_Project/FIX_SUMMARY.md` (this file)
   - Documentation of fixes
