# Scripts Directory

This directory contains development and testing scripts for the CareerBridge project.

## Scripts Overview

### Data Creation Scripts
- `create_test_data.py` - Creates comprehensive test data for all models
- `create_resume_test_data.py` - Creates test resume data and analysis
- `create_user_resumes.py` - Creates test users and their resumes
- `create_verified_user.py` - Creates a verified user for testing

### Testing Scripts
- `test_resumes.py` - Tests resume-related functionality
- `test_mentors.py` - Tests mentor-related functionality
- `test_referral_system.py` - Tests referral system functionality
- `test_tier_functionality.py` - Tests tier-based subscription functionality

## Usage

These scripts are for development and testing purposes only. They should not be used in production.

### Running Scripts
```bash
# From the careerbridge directory
python3 scripts/create_test_data.py
python3 scripts/test_resumes.py
```

### Notes
- These scripts may create test data in the database
- Some scripts require specific database state to run properly
- Always backup your database before running these scripts
- These scripts are not part of the main application code

## Maintenance

- Keep these scripts updated when models change
- Remove obsolete scripts when they're no longer needed
- Add new scripts here for development and testing tasks 