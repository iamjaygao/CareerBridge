# CareerBridge - AI-Powered Career Platform

## Overview

CareerBridge is a comprehensive career development platform that connects job seekers with AI-powered resume analysis, mentor services, and personalized job recommendations. The platform integrates external AI services for enhanced functionality while maintaining a robust, scalable architecture.

## Features

### Core Features
- **Resume Analysis**: AI-powered resume scoring and feedback using OpenAI
- **Mentor Services**: Book sessions with industry experts
- **Job Recommendations**: Personalized job matching based on resume analysis
- **Payment Processing**: Stripe integration for secure transactions
- **External Service Integration**: Modular API-based integration with ResumeMatcher and JobCrawler

### Advanced Features
- **Stripe Connect**: Mentor payout system with configurable platform fees
- **Legal Compliance**: GDPR-compliant data deletion and export functionality
- **Circuit Breaker**: Resilient external service integration with metrics
- **Docker Deployment**: Containerized application with production-ready configuration
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions

## Recent Optimizations (P2)

### Performance & UX Improvements
- **Unified Pagination**: All list pages (mentors, resumes, appointments) now use consistent pagination with 20 items per page
- **Popular Data Caching**: Implemented 5-minute TTL cache for popular jobs, skills, and industries to reduce API calls
- **Pre-fetching**: Popular data is pre-loaded on app initialization for faster dashboard rendering
- **Enhanced Dashboard**: Added trending data section showing popular jobs, skills, and industries with visual chips
- **Payment UX**: Improved payment demo page with loading states, error handling, and success feedback

### Technical Enhancements
- **DRF Pagination**: Configured default PageNumberPagination with 20 items per page for consistent API responses
- **Frontend Resilience**: Enhanced error handling with retry logic for external service calls
- **Cache Management**: Centralized cache utilities with automatic TTL expiration and manual refresh capabilities

## External Service Integration

### ResumeMatcher
- **Purpose**: AI-powered resume-to-job matching using semantic analysis
- **Integration**: RESTful API proxy with circuit breaker protection
- **Features**: Confidence scoring, explainable matches, skill alignment

### JobCrawler
- **Purpose**: Automated job data collection from multiple sources
- **Integration**: Scheduled ETL pipeline with data normalization
- **Sources**: LinkedIn, Indeed, RemoteOK, Glassdoor

## Payment Integration

### Stripe PaymentIntents
- **Secure Processing**: Tokenized payment handling with PCI compliance
- **Idempotency**: Prevents duplicate charges with unique keys
- **Webhooks**: Real-time payment status updates and refund processing

### Stripe Connect for Mentors
- **Onboarding**: Express account creation with KYC verification
- **Payouts**: Direct transfers to mentor accounts with configurable fees
- **Status Tracking**: Real-time KYC and capability status updates

## Legal Compliance

### Data Rights Management
- **Data Deletion**: User-initiated account deletion with verification
- **Data Export**: Asynchronous export with secure signed URLs
- **Privacy Rights**: Comprehensive privacy information and controls

## Deployment

### Docker Setup
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
```bash
# External Services
JOB_CRAWLER_API_KEY=your_key
RESUME_MATCHER_API_KEY=your_key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring
SENTRY_DSN=https://...

# Storage (Optional)
USE_S3=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
```

## Development

### Backend Setup
```bash
cd careerbridge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### External Services
The platform is designed to work with external ResumeMatcher and JobCrawler services. These can be:
- Deployed as separate microservices
- Integrated via API proxies
- Mocked for development using the provided test endpoints

## Testing

### Backend Tests
```bash
python manage.py test
```

### Frontend Tests
```bash
npm test
```

### E2E Testing
See `DEPLOYMENT.md` for comprehensive staging environment testing checklist.

## Monitoring & Observability

### Circuit Breaker Metrics
- **Debug Endpoint**: `/api/v1/services/metrics/` (admin only)
- **Sentry Integration**: Error tracking and performance monitoring
- **Health Checks**: External service availability monitoring

### Performance Monitoring
- **Frontend**: Performance monitoring with error boundaries
- **Backend**: Request/response logging with Sentry integration
- **External Services**: Circuit breaker with fallback mechanisms

## Security

### Production Security Checklist
- [ ] HTTPS enforcement with HSTS
- [ ] Secure cookie configuration
- [ ] CORS policy implementation
- [ ] Rate limiting on external service endpoints
- [ ] Input validation and sanitization
- [ ] Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository or contact the development team. 