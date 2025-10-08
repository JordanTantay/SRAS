# SRAS Login System Setup

## Overview
The SRAS system now includes a complete login system with:
- **Login Page**: Serves as the landing page (`/`)
- **Dashboard**: Main admin interface after login (`/dashboard/`)
- **Protected Views**: All violation management views require authentication
- **Navigation**: Consistent navigation across all pages

## Setup Instructions

### 1. Create Admin User
Run the following command to create an admin user:

```bash
cd SRAS_Project
python create_admin.py
```

This will create a user with:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

### 2. Alternative: Use Django Management Command
If the script doesn't work, you can create the user manually:

```bash
cd SRAS_Project
python manage.py shell
```

Then in the Python shell:
```python
from django.contrib.auth.models import User
User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='admin123',
    is_staff=True,
    is_superuser=True
)
exit()
```

### 3. Start the Development Server
```bash
cd SRAS_Project
python manage.py runserver
```

### 4. Access the System
1. Open your browser and go to `http://localhost:8000`
2. You'll see the login page
3. Use the credentials:
   - Username: `admin`
   - Password: `admin123`
4. After successful login, you'll be redirected to the dashboard

## System Features

### Login Page (`/`)
- Modern, responsive design
- Form validation
- Error message display
- Automatic redirect if already logged in

### Dashboard (`/dashboard/`)
- Overview statistics (total, today, this week, this month)
- Quick action cards
- Recent violations list
- Navigation to all system features

### Protected Views
All views now require authentication:
- **Live Monitor**: `/monitor/`
- **Violation List**: `/violations/`
- **Violation Details**: `/violations/<id>/`
- **Statistics API**: `/api/statistics/`

### Navigation
Consistent navigation bar on all pages:
- Dashboard
- Live Monitor
- Violations
- User dropdown with logout option

## Security Features

### Authentication
- All views protected with `@login_required` decorator
- Automatic redirect to login page for unauthenticated users
- Session-based authentication

### CSRF Protection
- All forms include CSRF tokens
- POST requests properly protected

### Password Security
- **Important**: Change the default password after first login
- Use Django's password change functionality:
  ```bash
  python manage.py changepassword admin
  ```

## File Structure

```
SRAS_Project/
├── SRAS_App/
│   ├── views.py          # Updated with login views
│   ├── urls.py           # Updated with login URLs
│   └── templates/core/
│       ├── login.html    # New login page
│       ├── dashboard.html # New dashboard
│       ├── monitor.html  # Updated with navigation
│       ├── violation_list.html # Updated with navigation
│       └── violation_detail.html # Updated with navigation
├── SRAS_Project/
│   └── settings.py       # Updated with login settings
├── create_admin.py       # Admin user creation script
└── LOGIN_SETUP.md        # This file
```

## Troubleshooting

### Common Issues

1. **"No module named 'django'"**
   - Make sure you're in the correct directory
   - Activate your virtual environment if using one

2. **Database connection errors**
   - Ensure MySQL is running
   - Check database credentials in settings.py

3. **Login not working**
   - Verify the admin user was created successfully
   - Check the credentials are correct
   - Clear browser cache if needed

4. **Navigation not showing**
   - Ensure Bootstrap CSS and JS are loading
   - Check browser console for JavaScript errors

### Testing the System

1. **Test Login Flow**:
   - Go to `http://localhost:8000`
   - Try logging in with wrong credentials (should show error)
   - Login with correct credentials (should redirect to dashboard)

2. **Test Protected Views**:
   - Try accessing `/monitor/` without login (should redirect to login)
   - After login, all views should be accessible

3. **Test Navigation**:
   - Navigate between all pages using the navigation bar
   - Test the logout functionality

## Customization

### Changing Default Password
After first login, change the password:
```bash
python manage.py changepassword admin
```

### Adding More Users
You can create additional users through:
- Django admin interface (`/admin/`)
- Django management commands
- Programmatically in Python shell

### Styling Customization
All templates use Bootstrap 5 and Font Awesome icons. You can customize:
- Colors in CSS variables
- Layout in template files
- Icons by changing Font Awesome classes

## Production Considerations

For production deployment:
1. Change `DEBUG = False` in settings.py
2. Set a strong `SECRET_KEY`
3. Configure proper database settings
4. Use HTTPS
5. Set up proper static file serving
6. Change all default passwords
7. Configure proper logging
8. Set up backup procedures 