# SRAS Database Integration Guide

## 🗄️ MySQL Database Integration

The SRAS system now automatically saves detected violations directly to your MySQL database with timestamps.

### ✨ New Features

1. **Automatic Database Storage**: Violations are saved to MySQL with timestamps
2. **Plate Number Detection**: Extracts and stores plate numbers when detected
3. **Real-time Statistics**: Live violation statistics with 5-day graphs
4. **Camera Management**: Automatic camera registration and tracking

### 🚀 Quick Setup

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Setup MySQL Database
```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE sras_django;
EXIT;

# Run setup script
python setup_mysql.py
```

#### 3. Start the System
```bash
# Terminal 1: Start Django server
python manage.py runserver

# Terminal 2: Start stream server
python stream_mjpeg.py
```

#### 4. Access the System
- **Monitor**: http://localhost:8000/monitor/

### 📊 Database Schema

#### Violation Table
```sql
CREATE TABLE `SRAS_App_violation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `camera_id` bigint NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `image` varchar(100) NOT NULL,
  `sms_sent` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `SRAS_App_violation_camera_id_fkey` (`camera_id`),
  CONSTRAINT `SRAS_App_violation_camera_id_fkey` FOREIGN KEY (`camera_id`) REFERENCES `SRAS_App_camera` (`id`)
);
```

#### Camera Table
```sql
CREATE TABLE `SRAS_App_camera` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `stream_url` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
);
```

### 🔧 Configuration

#### Database Settings (settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sras_django',
        'USER': 'root',
        'PASSWORD': '',  # Add your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

#### Camera Configuration (stream_mjpeg.py)
```python
# Update your camera URL
cap = cv2.VideoCapture("http://192.168.1.4:8080/video")
```

### 📈 Statistics API

#### Endpoint: `/api/statistics/`
Returns violation statistics for the last 5 days:

```json
{
  "statistics": [
    {
      "date": "2024-01-15",
      "display_date": "15 Jan",
      "count": 5
    },
    {
      "date": "2024-01-16", 
      "display_date": "16 Jan",
      "count": 3
    }
  ],
  "total_violations": 25
}
```

### 🎯 Features

#### Automatic Violation Detection
- ✅ Detects no-helmet riders
- ✅ Captures violation images
- ✅ Saves to MySQL with timestamp
- ✅ Extracts plate numbers (if detected)
- ✅ Prevents duplicate captures

#### Real-time Statistics
- 📊 5-day violation graph
- 📅 Date-based display (01 Jan, 02 Jan, etc.)
- 🔄 Auto-refresh every 5 minutes
- 📱 Responsive design

#### Database Integration
- 🗄️ MySQL storage with timestamps
- 📸 Image file management
- 🔗 Camera relationship tracking
- 📊 Statistical analysis ready

### 🛠️ Troubleshooting

#### MySQL Connection Issues
```bash
# Install alternative MySQL client
pip install pymysql

# Add to settings.py
import pymysql
pymysql.install_as_MySQLdb()
```

#### Database Migration Issues
```bash
# Reset migrations
python manage.py migrate SRAS_App zero
python manage.py makemigrations
python manage.py migrate
```

#### Stream Server Issues
```bash
# Check camera connection
python -c "import cv2; cap = cv2.VideoCapture('http://192.168.1.4:8080/video'); print('Connected:', cap.isOpened())"
```

### 📋 Monitoring

#### Check Database Records
```python
# Django shell
python manage.py shell

from SRAS_App.models import Violation
violations = Violation.objects.all().order_by('-timestamp')
for v in violations[:5]:
    print(f"ID: {v.id}, Time: {v.timestamp}, Plate: {v.plate_number}")
```

#### View Statistics
- Visit: http://localhost:8000/monitor/
- Statistics section shows live violation data
- Graph updates automatically

### 🔒 Security Notes

- ⚠️ Change default MySQL password
- 🔐 Use environment variables for database credentials
- 🛡️ Enable MySQL authentication
- 📁 Secure media directory permissions

### 📞 Support

For issues with:
- **Database**: Check MySQL server status and credentials
- **Detection**: Verify camera URL and YOLO models
- **Statistics**: Ensure Django server is running
- **Stream**: Check port 8081 availability

---

**🎉 Your SRAS system is now fully integrated with MySQL database!** 