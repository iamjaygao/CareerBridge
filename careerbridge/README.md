# CareerBridge

A comprehensive career development platform that provides resume analysis, job matching, mentorship, and career guidance services.

## 🚀 Features

### Core Functionality
- **Resume Management**: Upload, analyze, and optimize resumes with AI-powered insights
- **Job Matching**: Match resumes with job descriptions using advanced algorithms
- **Mentorship System**: Connect with industry mentors for career guidance
- **Appointment Booking**: Schedule and manage mentoring sessions
- **Tier-based Services**: Free, Premium, and Enterprise subscription tiers
- **Referral Program**: Invite friends and earn rewards

### Legal Compliance & Data Protection
- **GDPR/CCPA Compliance**: User consent management and data rights
- **Data Retention Policies**: Automated data lifecycle management
- **Privacy Controls**: Granular consent for data collection and processing
- **Right to be Forgotten**: User-initiated data deletion requests
- **Legal Disclaimers**: Comprehensive terms and privacy policies

### Technical Features
- **RESTful API**: Complete API documentation with Swagger/OpenAPI
- **JWT Authentication**: Secure token-based authentication
- **File Management**: Secure resume file upload and storage
- **External Service Integration**: Microservices architecture for scalability
- **Automated Testing**: Comprehensive test coverage

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Django 5.2+
- SQLite (development) / PostgreSQL (production)

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CareerBridge/careerbridge
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv myvenv
   source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Documentation

### Swagger UI
Access the interactive API documentation at: http://localhost:8000/swagger/

### ReDoc
Alternative API documentation at: http://localhost:8000/redoc/

### API Endpoints
- **Users**: `/api/v1/users/` - Registration, authentication, profile management
- **Resumes**: `/api/v1/resumes/` - Resume upload, analysis, comparison
- **Mentors**: `/api/v1/mentors/` - Mentor profiles, availability, reviews
- **Appointments**: `/api/v1/appointments/` - Booking and session management
- **Admin Panel**: `/api/v1/adminpanel/` - Administrative functions
- **Notifications**: `/api/v1/notifications/` - User notifications

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: List of allowed hostnames
- `EMAIL_HOST_USER`: Email configuration for notifications
- `EMAIL_HOST_PASSWORD`: Email password/app password

### External Services
The platform is designed to integrate with external microservices:
- **Job Crawler Service**: For fetching job postings
- **Resume Matcher Service**: For advanced matching algorithms
- **AI Analysis Service**: For enhanced resume analysis

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test resumes
python manage.py test users
python manage.py test mentors
```

### Test Coverage
- Model tests for all apps
- API endpoint tests
- Service layer tests
- Legal compliance tests

## 📋 Legal Compliance

### Data Protection
- **User Consent**: Track and manage user consent for data processing
- **Data Retention**: Automated deletion based on configured policies
- **Data Rights**: Support for GDPR/CCPA data subject rights
- **Privacy Policy**: Comprehensive privacy policy management

### Compliance Features
- Consent tracking for data collection, processing, and sharing
- Automated data retention and deletion
- User-initiated data deletion requests
- Legal disclaimer management
- Audit trails for compliance

## 🏗️ Architecture

### Project Structure
```
careerbridge/
├── careerbridge/          # Main project settings
├── users/                 # User management and authentication
├── resumes/              # Resume management and analysis
├── mentors/              # Mentor profiles and availability
├── appointments/         # Booking and session management
├── notifications/        # User notification system
├── adminpanel/          # Administrative functions
└── media/               # File storage
```

### Key Models
- **User**: Extended user model with subscription and referral tracking
- **Resume**: Resume storage and analysis results
- **ResumeComparison**: Multi-resume comparison functionality
- **UserSubscription**: Tier-based subscription management
- **UserDataConsent**: Legal compliance tracking
- **DataRetentionPolicy**: Automated data lifecycle management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Email: contact@careerbridge.com
- Documentation: http://localhost:8000/swagger/
- Issues: GitHub Issues page

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core functionality
- Legal compliance features
- API documentation
- Tier-based subscription system
- Referral program
- External service integration framework

---

**Note**: This is a development version. For production deployment, ensure all security settings are properly configured and external services are integrated. 