# SRAS Enforcer Management System

## Overview
The SRAS system now includes a comprehensive enforcer management system that allows administrators to:
- **Register new enforcers** with unique usernames and passwords
- **Assign cameras** to specific enforcers
- **Manage enforcer status** (active/inactive)
- **Edit enforcer information** including contact details
- **Delete enforcers** when needed

## New Features

### Dashboard Updates
- **Replaced Statistics button** with "Add Enforcer" button
- **Added enforcer statistics** showing total and active enforcers
- **Enhanced navigation** with Enforcers menu item

### Enforcer Management
- **Enforcer List**: View all registered enforcers
- **Add Enforcer**: Register new enforcers with full details
- **Edit Enforcer**: Update enforcer information and status
- **Delete Enforcer**: Remove enforcers from the system

## Setup Instructions

### 1. Add Sample Cameras (Optional)
If you want to test camera assignment functionality:

```bash
cd SRAS_Project
python add_sample_cameras.py
```

This will create 4 sample cameras for testing.

### 2. Access the System
1. Start the development server:
   ```bash
   cd SRAS_Project
   python manage.py runserver
   ```

2. Login with admin credentials:
   - Username: `admin`
   - Password: `admin123`

3. Navigate to the dashboard and click "Add Enforcer"

## Enforcer Registration Process

### Required Information
- **Username**: Unique login name (cannot be changed later)
- **Email**: Contact email address
- **Password**: Secure login password
- **Mobile Number**: Contact number for notifications
- **Assigned Camera**: Optional camera assignment

### Enforcer Permissions
- Enforcers can log into the system
- They can view violations and monitor feeds
- They cannot add/edit/delete other enforcers
- They cannot access admin functions

## File Structure

```
SRAS_Project/
├── SRAS_App/
│   ├── views.py              # Updated with enforcer views
│   ├── urls.py               # Updated with enforcer URLs
│   └── templates/core/
│       ├── dashboard.html    # Updated with enforcer stats
│       ├── add_enforcer.html # New enforcer registration
│       ├── enforcer_list.html # Enforcer management list
│       ├── edit_enforcer.html # Edit enforcer form
│       └── [existing templates] # Updated with navigation
├── add_sample_cameras.py     # Sample camera creation script
└── ENFORCER_SETUP.md        # This file
```

## Usage Guide

### Adding a New Enforcer
1. Go to Dashboard → Click "Add Enforcer"
2. Fill in the required information:
   - Username (unique)
   - Email address
   - Password (minimum 8 characters recommended)
   - Mobile number
   - Optional camera assignment
3. Click "Create Enforcer"
4. Enforcer will be created and can immediately log in

### Managing Enforcers
1. Go to Dashboard → Click "Enforcers" in navigation
2. View all registered enforcers
3. Click "Edit" to modify enforcer details
4. Click "Delete" to remove enforcers

### Enforcer Status
- **Active**: Enforcer can log in and use the system
- **Inactive**: Enforcer account is disabled
- Status can be toggled in the edit form

### Camera Assignment
- Enforcers can be assigned to specific cameras
- This helps track which enforcer is monitoring which location
- Assignment is optional and can be changed

## Security Features

### Authentication
- Each enforcer has unique login credentials
- Passwords are securely hashed
- Session-based authentication

### Access Control
- Enforcers can only access their assigned features
- Admin functions are restricted to admin users
- Proper CSRF protection on all forms

### Data Protection
- Enforcer information is stored securely
- Mobile numbers are validated
- Email addresses are verified format

## Testing the System

### 1. Create Test Enforcers
1. Login as admin
2. Go to Dashboard → Add Enforcer
3. Create a test enforcer with:
   - Username: `enforcer1`
   - Email: `enforcer1@example.com`
   - Password: `enforcer123`
   - Mobile: `+1234567890`

### 2. Test Enforcer Login
1. Logout from admin account
2. Login with enforcer credentials
3. Verify enforcer can access appropriate features

### 3. Test Management Functions
1. Login as admin
2. Go to Enforcers list
3. Test edit and delete functions
4. Verify status changes work

## Troubleshooting

### Common Issues

1. **"Username already exists"**
   - Choose a different username
   - Usernames must be unique

2. **"Invalid email format"**
   - Ensure email follows standard format
   - Example: `user@example.com`

3. **"Password too short"**
   - Use at least 8 characters
   - Include letters and numbers

4. **"Mobile number invalid"**
   - Use standard phone number format
   - Include country code if needed

### Database Issues

1. **No cameras available**
   - Run `python add_sample_cameras.py`
   - Or create cameras through Django admin

2. **Enforcer not appearing in list**
   - Check if enforcer was created successfully
   - Verify database connection

### Navigation Issues

1. **Enforcers link not showing**
   - Clear browser cache
   - Check if Bootstrap CSS is loading

2. **Forms not submitting**
   - Check browser console for JavaScript errors
   - Verify CSRF token is present

## Production Considerations

### Security
1. Change default admin password
2. Use strong passwords for all enforcers
3. Enable HTTPS in production
4. Set up proper logging

### Performance
1. Add database indexes for enforcer queries
2. Implement pagination for large enforcer lists
3. Cache frequently accessed data

### Monitoring
1. Set up alerts for failed login attempts
2. Monitor enforcer activity
3. Track camera assignments

## API Endpoints

The system includes these new endpoints:
- `GET /enforcers/` - List all enforcers
- `GET /enforcers/add/` - Add enforcer form
- `POST /enforcers/add/` - Create enforcer
- `GET /enforcers/<id>/edit/` - Edit enforcer form
- `POST /enforcers/<id>/edit/` - Update enforcer
- `POST /enforcers/<id>/delete/` - Delete enforcer

All endpoints require admin authentication. 