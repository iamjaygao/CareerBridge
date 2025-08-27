# Role Management Update - Complete Implementation

## Overview
Updated the user management system to properly handle user roles and staff status as separate concepts.

## Role System Design

### Backend Roles (User Model)
The backend supports three main roles defined in `careerbridge/users/models.py`:

```python
ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('mentor', 'Mentor'), 
    ('student', 'Student'),
)
```

### Staff Status
Staff status (`is_staff`) is a separate boolean field that provides additional administrative permissions, independent of the user's role.

## Updated Features

### 1. User Display
- **Status Column**: Shows Active/Inactive status (green/red chips)
- **Role Column**: Shows user role with color coding:
  - **Admin**: Red chip
  - **Mentor**: Blue chip  
  - **Student**: Gray chip
- **Staff Indicator**: Additional purple "Staff" chip for users with `is_staff=True`

### 2. Role Filtering
- **Role Filter**: Filter users by role (Student, Mentor, Admin)
- **Status Filter**: Filter users by status (Active, Inactive)
- **Combined Filters**: Multiple filters can be applied simultaneously

### 3. User Creation
- **Role Selection**: Dropdown with Student, Mentor, Admin options
- **Staff Toggle**: Checkbox to grant additional staff permissions
- **Validation**: Ensures valid role selection

### 4. User Editing
- **Role Update**: Change user role between Student, Mentor, Admin
- **Staff Toggle**: Enable/disable staff permissions
- **Form Pre-population**: Current role and staff status loaded into form

## Backend API Updates

### User Management API (`/api/v1/adminpanel/users/`)
- **GET**: Now returns `role` field for all users
- **POST create**: Accepts `role` parameter (student/mentor/admin)
- **POST update**: Updates both `role` and `is_staff` fields

### Database Schema
- **role**: CharField with choices (admin, mentor, student)
- **is_staff**: BooleanField for additional permissions
- **is_active**: BooleanField for account status

## Frontend Updates

### User Interface
- **Table Columns**: Separate columns for Status and Role
- **Visual Indicators**: Color-coded chips for different roles
- **Form Fields**: Role dropdown and staff checkbox in create/edit dialogs

### TypeScript Interfaces
```typescript
interface User {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  role?: string;  // Added role field
  date_joined: string;
  last_login: string;
  total_appointments: number;
  total_resumes: number;
}
```

## Role Hierarchy and Permissions

### Admin Role
- Full system access
- User management
- System configuration
- Content moderation

### Mentor Role  
- Profile management
- Appointment scheduling
- Student interactions
- Earnings tracking

### Student Role
- Basic user features
- Resume upload
- Appointment booking
- Profile management

### Staff Status (Additional)
- Administrative dashboard access
- Enhanced permissions
- Can be combined with any role

## Usage Examples

### Creating Different User Types

1. **Admin User**:
   ```json
   {
     "username": "admin_user",
     "email": "admin@example.com", 
     "password": "secure_password",
     "role": "admin",
     "is_staff": true
   }
   ```

2. **Mentor User**:
   ```json
   {
     "username": "mentor_user",
     "email": "mentor@example.com",
     "password": "secure_password", 
     "role": "mentor",
     "is_staff": false
   }
   ```

3. **Student User**:
   ```json
   {
     "username": "student_user",
     "email": "student@example.com",
     "password": "secure_password",
     "role": "student", 
     "is_staff": false
   }
   ```

### Filtering Users

- **All Students**: Role filter = "student"
- **All Mentors**: Role filter = "mentor"  
- **All Admins**: Role filter = "admin"
- **Staff Members**: Look for users with purple "Staff" chip
- **Active Users**: Status filter = "active"

## Security Considerations

### Role-Based Access Control
- Frontend routes protected by role requirements
- Backend API endpoints validate user permissions
- Admin-only features require admin role

### Staff Permissions
- Staff status provides additional administrative access
- Can be granted independently of user role
- Useful for temporary administrative access

## Future Enhancements

### 1. Advanced Role Management
- Custom role creation
- Role-based permissions matrix
- Role inheritance

### 2. Permission System
- Granular permissions per role
- Permission groups
- Dynamic permission assignment

### 3. Role Analytics
- Role distribution statistics
- Role-based activity tracking
- Performance metrics by role

## Testing

### Manual Testing Checklist
- [ ] Create user with each role (student, mentor, admin)
- [ ] Edit user role and staff status
- [ ] Filter users by role and status
- [ ] Verify role display in user list
- [ ] Test role-based access control

### API Testing
```bash
# Get users with roles
curl -X GET http://127.0.0.1:8000/api/v1/adminpanel/users/ \
  -H "Authorization: Bearer <token>"

# Create admin user
curl -X POST http://127.0.0.1:8000/api/v1/adminpanel/users/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "create", "username": "new_admin", "email": "admin@test.com", "password": "password123", "role": "admin"}'
```

## Migration Notes

### Database Changes
- No new migrations required (role field already exists)
- Existing users have default role = "student"
- Staff status preserved for existing admin users

### Frontend Changes
- Updated User interface to include role field
- Modified user management components
- Enhanced filtering and display logic

---

This update provides a complete and flexible role management system that separates user roles from staff permissions, allowing for fine-grained access control and user categorization. 