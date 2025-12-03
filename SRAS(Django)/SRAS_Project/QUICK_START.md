# Quick Start Guide - After Fixes

## What Was Fixed

1. ✅ **Android verification endpoint** - Users can now approve/reject violations from mobile app
2. ✅ **Enforcer chart red legend** - Dashboard now shows inactive enforcers in red

## Start the Server

```bash
cd "SRAS(Django)/SRAS_Project"
python manage.py runserver
```

## Test the Fixes

### 1. Check Dashboard (2 minutes)
1. Open browser: `http://localhost:8000/`
2. Login as admin
3. Look at the "Enforcer Status" chart on the right
4. **Expected**: You should see green (Active: 4) and red (Inactive: 1) segments

### 2. Test Android App Verification (5 minutes)
1. Open SRAS2 Android app
2. Login with credentials
3. Tap "Pending Verifications"
4. Select a violation
5. Tap "Approve" or "Reject"
6. **Expected**: Success message, violation disappears from list

### 3. Verify API Works (1 minute)
```bash
# Get your token first
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Test pending violations endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/violations/pending/
```

## Common Issues

### "No pending violations"
- This is normal if all violations have been verified
- Wait for new violations from the detection system
- Or create test data: `python manage.py create_test_pending_violations`

### Android app shows "Network error"
- Check Django server is running
- Update base URL in `SRAS2/app/src/main/java/com/example/sras/api/ApiService.kt`
- Make sure your phone/emulator can reach the server IP

### Chart still shows 0 inactive
- Hard refresh browser (Ctrl+Shift+R)
- Check browser console for errors
- Verify server restarted after changes

## Need More Help?

Run the test script:
```bash
cd "SRAS(Django)/SRAS_Project"
python test_verification_fix.py
```

Check the detailed documentation:
- `FIX_SUMMARY.md` - Complete technical details
- `VERIFICATION_WORKFLOW.md` - How verification works
