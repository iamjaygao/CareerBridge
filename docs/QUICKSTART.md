# CareerBridge Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)
- Database (SQLite for development, PostgreSQL for production)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd CareerBridge

# Create virtual environment
python -m venv myvenv
source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp careerbridge/env_template.txt .env

# Edit .env file with your settings
# For development, you can use default values
```

### 3. Initialize Project

```bash
# Run the initialization script
python careerbridge/scripts/init_project.py
```

This script will:
- ✅ Check database connection
- ✅ Run migrations
- ✅ Create superuser (admin/admin123)
- ✅ Generate test data
- ✅ Set up system configuration

### 4. Start Development Server

```bash
python careerbridge/manage.py runserver
```

## 📱 Access Points

### Admin Interface
- **URL**: http://127.0.0.1:8000/admin/
- **Username**: admin
- **Password**: admin123

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/

### API Endpoints
- **Users**: http://127.0.0.1:8000/api/v1/users/
- **Mentors**: http://127.0.0.1:8000/api/v1/mentors/
- **Appointments**: http://127.0.0.1:8000/api/v1/appointments/
- **Resumes**: http://127.0.0.1:8000/api/v1/resumes/
- **Notifications**: http://127.0.0.1:8000/api/v1/notifications/
- **Admin Panel**: http://127.0.0.1:8000/api/v1/adminpanel/

## 🧪 Test Data

The initialization script creates test data including:

### Users
- **Mentors**: john_mentor, sarah_mentor, mike_mentor
- **Students**: alice_student, bob_student
- **Admin**: admin

### Test Credentials
All test users have password: `testpass123`

## 🔧 Development Commands

```bash
# Run tests
python careerbridge/manage.py test

# Create migrations
python careerbridge/manage.py makemigrations

# Apply migrations
python careerbridge/manage.py migrate

# Create superuser
python careerbridge/manage.py createsuperuser

# Generate test data
python careerbridge/scripts/create_test_data.py

# Check code quality
python careerbridge/manage.py check
```

## 📊 Admin Features

### System Statistics
- User statistics (total, active, new users)
- Mentor statistics (total, active, pending applications)
- Appointment statistics (total, completed, cancelled)
- Revenue statistics
- System performance metrics

### User Management
- View all users with statistics
- Activate/deactivate users
- Manage user roles (admin, mentor, student)

### Mentor Management
- Approve/reject mentor applications
- View mentor profiles and statistics
- Manage mentor services and availability

### Appointment Management
- View all appointments
- Manage appointment status
- Track payments and cancellations

### Content Moderation
- Review flagged content
- Approve/reject user-generated content
- Track moderation actions

### Data Export
- Export user data
- Export mentor data
- Export appointment data
- Multiple formats (CSV, JSON, Excel, PDF)

## 🔐 Security Features

- Admin action logging
- IP address tracking
- User agent logging
- Sensitive data protection
- Content moderation system

## 📈 Monitoring

### System Health
- Database status
- Cache status
- External services status
- Disk usage
- Memory usage
- CPU usage
- Active connections
- Error rates

### Performance Metrics
- Average response time
- Error rate
- Uptime percentage
- User activity metrics

## 🚀 Next Steps

1. **Explore the Admin Interface**
   - Navigate through different sections
   - Test the management features
   - Review system statistics

2. **Test API Endpoints**
   - Use Swagger UI to test APIs
   - Create test requests
   - Verify responses

3. **Review Test Data**
   - Check created users and mentors
   - Review appointments and reviews
   - Examine system configurations

4. **Customize Configuration**
   - Modify system settings in admin
   - Update notification templates
   - Configure payment settings

## 📚 Documentation

- **README.md**: Project overview and architecture
- **DEPLOYMENT.md**: Production deployment guide
- **scripts/README.md**: Available scripts and utilities
- **API Documentation**: Available via Swagger UI

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check database settings in settings.py
   - Ensure database is running
   - Verify connection credentials

2. **Migration Errors**
   - Delete migration files and recreate
   - Check for model conflicts
   - Verify database schema

3. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check STATIC_URL and STATIC_ROOT settings

4. **Permission Errors**
   - Check file permissions
   - Ensure virtual environment is activated
   - Verify Python path

### Getting Help

- Check the logs in `careerbridge/logs/`
- Review Django debug information
- Consult API documentation
- Check system configuration in admin panel

## 🎯 Success Indicators

You know the setup is working when:

- ✅ Admin interface loads without errors
- ✅ API documentation is accessible
- ✅ Test data is visible in admin
- ✅ All management features work
- ✅ System statistics are populated
- ✅ No error messages in console

---

**Happy Coding! 🚀** 