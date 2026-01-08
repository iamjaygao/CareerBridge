# Mentor Profile Creation Defaults Fix

**Date**: 2026-01-07  
**Type**: Backend Fix (Django REST Framework)  
**Status**: ✅ COMPLETED

---

## Problem Statement

### Root Cause
The mentor profile creation endpoint (`POST /api/v1/human-loop/profile/`) was **returning 400 Bad Request** because it required too many fields from the frontend that should have been set as **system defaults**.

**Specific Issues**:
1. Using `MentorProfileDetailSerializer` for creation (designed for updates, not creation)
2. No explicit system defaults being set for required fields
3. Frontend had to provide all fields, including system-managed ones
4. Fields like `status`, `timezone`, `starting_price`, ratings, earnings, etc. should be auto-set
5. Created profiles had incorrect initial state

### The Requirement

A mentor profile should be created with **minimal user input**:
- **User provides**: `bio`, `current_position`, `industry` (required)
- **User optionally provides**: `years_of_experience`, `primary_focus`, `session_focus`, `specializations`
- **System automatically sets**: status, timezone, pricing, ratings, earnings, verification flags, payment flags

---

## Solution

We created a dedicated **`MentorProfileCreateSerializer`** that:
1. Only requires minimal user-editable fields
2. Automatically sets system defaults in the `create()` method
3. Returns clear success response with `mentor_profile_id`

---

## Implementation Details

### 1. Created New Serializer for Profile Creation

**File**: `gateai/human_loop/serializers.py`

**New Serializer**: `MentorProfileCreateSerializer`

```python
class MentorProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for CREATING a new mentor profile.
    
    Only requires user-editable fields. System defaults are set automatically.
    """
    # User-editable fields (minimal required set)
    bio = serializers.CharField(required=True, max_length=500)
    current_position = serializers.CharField(required=True, max_length=200)
    industry = serializers.CharField(required=True, max_length=100)
    years_of_experience = serializers.IntegerField(required=False, default=0)
    
    # Optional user-editable fields
    primary_focus = serializers.CharField(required=False, allow_blank=True, max_length=100)
    session_focus = serializers.CharField(required=False, allow_blank=True, max_length=150)
    specializations = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    class Meta:
        model = MentorProfile
        fields = (
            'bio',
            'current_position',
            'industry',
            'years_of_experience',
            'primary_focus',
            'session_focus',
            'specializations',
        )
    
    def create(self, validated_data):
        """
        Create mentor profile with system defaults.
        
        System defaults are set automatically:
        - status = "draft"
        - timezone = user.timezone OR settings.TIME_ZONE OR "UTC"
        - starting_price = Decimal("0.00")
        - average_rating = Decimal("0.00")
        - total_reviews = 0
        - total_earnings = Decimal("0.00")
        - total_sessions = 0
        - is_verified = False
        - payouts_enabled = False
        - charges_enabled = False
        - specializations = [] (if not provided)
        """
        from decimal import Decimal
        from django.conf import settings
        
        user = validated_data.pop('user')
        
        # Set system defaults
        profile_data = {
            'user': user,
            'status': 'draft',  # Override default 'pending' - new profiles start as draft
            'timezone': getattr(user, 'timezone', None) or settings.TIME_ZONE or 'UTC',
            'starting_price': Decimal('0.00'),
            'average_rating': Decimal('0.00'),
            'total_reviews': 0,
            'total_earnings': Decimal('0.00'),
            'total_sessions': 0,
            'is_verified': False,
            'payouts_enabled': False,
            'charges_enabled': False,
        }
        
        # Add user-provided data
        profile_data.update(validated_data)
        
        # Ensure specializations is a list
        if 'specializations' not in profile_data:
            profile_data['specializations'] = []
        
        return MentorProfile.objects.create(**profile_data)
```

**Key Features**:
- **Required fields**: `bio`, `current_position`, `industry` (only user-visible fields)
- **Optional fields**: `years_of_experience`, `primary_focus`, `session_focus`, `specializations`
- **System defaults**: All system-managed fields set automatically
- **Explicit logic**: No silent failures, clear validation

---

### 2. Updated Profile Creation View

**File**: `gateai/human_loop/views.py`

**Updated View**: `MentorProfileCreateView`

```python
class MentorProfileCreateView(generics.CreateAPIView):
    """
    CREATE mentor profile for authenticated user.
    
    This endpoint is for CREATING a new mentor profile.
    Use PATCH /profile/update/ for updating an existing profile.
    
    System defaults are set automatically:
    - status = "draft"
    - timezone = user.timezone OR settings.TIME_ZONE OR "UTC"
    - starting_price = Decimal("0.00")
    - average_rating = Decimal("0.00")
    - total_reviews = 0
    - total_earnings = Decimal("0.00")
    - total_sessions = 0
    - is_verified = False
    - payouts_enabled = False
    - charges_enabled = False
    - specializations = []
    
    Returns 201 Created with mentor_profile_id on success.
    Returns 400 if profile already exists or validation fails.
    """
    serializer_class = MentorProfileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Check if profile already exists
        if hasattr(user, 'mentor_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': 'Mentor profile already exists. Use PATCH /profile/update/ to update it.'
            })
        
        # Create the profile with user
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        """Override to return mentor_profile_id in response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return created profile data with explicit mentor_profile_id
        profile = serializer.instance
        response_data = {
            'id': profile.id,
            'mentor_profile_id': profile.id,
            'status': profile.status,
            'message': 'Mentor profile created successfully',
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
```

**Changes**:
- Changed `serializer_class` from `MentorProfileDetailSerializer` to `MentorProfileCreateSerializer`
- Overrode `create()` to return explicit `mentor_profile_id` in response
- Added clear documentation of system defaults
- Returns 201 Created with structured response

---

### 3. Updated Imports

**File**: `gateai/human_loop/views.py`

```python
from .serializers import (
    MentorProfileSerializer, MentorProfileDetailSerializer, MentorProfileCreateSerializer,  # Added
    # ... other imports
)
```

---

## System Defaults Set Automatically

| Field | System Default | Source |
|-------|---------------|--------|
| `status` | `"draft"` | Hardcoded (overrides model default of "pending") |
| `timezone` | `user.timezone` OR `settings.TIME_ZONE` OR `"UTC"` | User preference → global setting → fallback |
| `starting_price` | `Decimal("0.00")` | Hardcoded |
| `average_rating` | `Decimal("0.00")` | Hardcoded |
| `total_reviews` | `0` | Hardcoded |
| `total_earnings` | `Decimal("0.00")` | Hardcoded |
| `total_sessions` | `0` | Hardcoded |
| `is_verified` | `False` | Hardcoded |
| `payouts_enabled` | `False` | Hardcoded |
| `charges_enabled` | `False` | Hardcoded |
| `specializations` | `[]` | Empty list if not provided |

---

## Request/Response Flow

### ✅ Successful Profile Creation

**Request**:
```http
POST /api/v1/human-loop/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Experienced software engineer with 10 years in tech",
  "current_position": "Senior Software Engineer at Google",
  "industry": "Technology"
}
```

**Response** (201 Created):
```json
{
  "id": 42,
  "mentor_profile_id": 42,
  "status": "draft",
  "message": "Mentor profile created successfully"
}
```

**Database State** (auto-set):
```python
MentorProfile(
    id=42,
    user=<User>,
    bio="Experienced software engineer with 10 years in tech",
    current_position="Senior Software Engineer at Google",
    industry="Technology",
    years_of_experience=0,  # Default
    status="draft",  # Auto-set
    timezone="America/New_York",  # From user or settings
    starting_price=Decimal("0.00"),  # Auto-set
    average_rating=Decimal("0.00"),  # Auto-set
    total_reviews=0,  # Auto-set
    total_earnings=Decimal("0.00"),  # Auto-set
    total_sessions=0,  # Auto-set
    is_verified=False,  # Auto-set
    payouts_enabled=False,  # Auto-set
    charges_enabled=False,  # Auto-set
    specializations=[],  # Auto-set
)
```

---

### ❌ Profile Already Exists

**Request**:
```http
POST /api/v1/human-loop/profile/
Authorization: Bearer <token>
```

**Response** (400 Bad Request):
```json
{
  "detail": "Mentor profile already exists. Use PATCH /profile/update/ to update it."
}
```

---

### ❌ Missing Required Fields

**Request**:
```http
POST /api/v1/human-loop/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Some bio"
  // Missing: current_position, industry
}
```

**Response** (400 Bad Request):
```json
{
  "current_position": ["This field is required."],
  "industry": ["This field is required."]
}
```

---

## Field Requirements Summary

### Required by User
- ✅ `bio` (CharField, max 500 chars)
- ✅ `current_position` (CharField, max 200 chars)
- ✅ `industry` (CharField, max 100 chars)

### Optional User Fields
- ⚪ `years_of_experience` (Integer, defaults to 0)
- ⚪ `primary_focus` (CharField, max 100 chars, blank allowed)
- ⚪ `session_focus` (CharField, max 150 chars, blank allowed)
- ⚪ `specializations` (List of strings, defaults to [])

### Set Automatically (NOT Required from Frontend)
- 🔒 `status` = "draft"
- 🔒 `timezone` = user.timezone OR settings.TIME_ZONE OR "UTC"
- 🔒 `starting_price` = Decimal("0.00")
- 🔒 `average_rating` = Decimal("0.00")
- 🔒 `total_reviews` = 0
- 🔒 `total_earnings` = Decimal("0.00")
- 🔒 `total_sessions` = 0
- 🔒 `is_verified` = False
- 🔒 `payouts_enabled` = False
- 🔒 `charges_enabled` = False
- 🔒 `specializations` = [] (if not provided)

---

## Design Principles

### 1. Explicit System Defaults
```python
# GOOD: Explicit default setting
profile_data = {
    'user': user,
    'status': 'draft',  # Explicit
    'starting_price': Decimal('0.00'),  # Explicit
}
```

```python
# BAD: Relying on model defaults (can be forgotten/changed)
MentorProfile.objects.create(user=user, bio=bio)  # What defaults apply?
```

### 2. Minimal User Input
- Only require what the user **must** provide
- Everything else is system-managed
- Clear separation of concerns

### 3. Timezone Fallback Chain
```python
timezone = getattr(user, 'timezone', None) or settings.TIME_ZONE or 'UTC'
```
1. Try user's timezone preference
2. Fall back to global setting
3. Ultimate fallback: UTC

### 4. Clear Response Structure
```python
response_data = {
    'id': profile.id,
    'mentor_profile_id': profile.id,  # Explicit for frontend
    'status': profile.status,  # Show initial state
    'message': 'Mentor profile created successfully',  # Clear message
}
```

---

## Testing Scenarios

### ✅ Scenario 1: New Mentor (Minimal Data)

**Request**:
```json
{
  "bio": "I'm a mentor",
  "current_position": "Engineer",
  "industry": "Tech"
}
```

**Expected**:
- ✅ 201 Created
- ✅ Profile created with all system defaults
- ✅ `status` = "draft"
- ✅ `years_of_experience` = 0
- ✅ `specializations` = []

---

### ✅ Scenario 2: New Mentor (Full Optional Data)

**Request**:
```json
{
  "bio": "Experienced mentor",
  "current_position": "Senior Engineer",
  "industry": "Technology",
  "years_of_experience": 10,
  "primary_focus": "Career Growth",
  "session_focus": "1-on-1 coaching",
  "specializations": ["Python", "System Design"]
}
```

**Expected**:
- ✅ 201 Created
- ✅ All user-provided fields saved
- ✅ System defaults still applied for other fields

---

### ✅ Scenario 3: Duplicate Profile Creation

**User State**: Already has mentor profile

**Expected**:
- ❌ 400 Bad Request
- ❌ Error: "Mentor profile already exists. Use PATCH /profile/update/ to update it."

---

### ✅ Scenario 4: Missing Required Field

**Request**:
```json
{
  "bio": "Test"
  // Missing: current_position, industry
}
```

**Expected**:
- ❌ 400 Bad Request
- ❌ Validation errors for missing fields

---

## Files Changed (2 files)

### Backend (2 files)
1. **`gateai/human_loop/serializers.py`**
   - Added `MentorProfileCreateSerializer` class
   - Defined minimal required fields
   - Implemented `create()` with system defaults
   - Clear documentation of all defaults

2. **`gateai/human_loop/views.py`**
   - Updated `MentorProfileCreateView` to use new serializer
   - Overrode `create()` to return structured response
   - Added `MentorProfileCreateSerializer` to imports
   - Clear documentation in view docstring

---

## Validation Checklist

- [x] POST `/profile/` creates profile successfully
- [x] Only requires bio, current_position, industry
- [x] Optional fields work correctly
- [x] System defaults are set automatically
- [x] status = "draft" (not "pending")
- [x] timezone uses fallback chain
- [x] Returns 201 with mentor_profile_id
- [x] Prevents duplicate profile creation (400)
- [x] Validation errors are clear
- [x] No database schema changes
- [x] No model constraint changes
- [x] Logic is explicit and readable
- [x] No linter errors (only pre-existing unrelated warning)

---

## Code Quality

### Explicit Default Setting
```python
# All defaults are explicit in code
profile_data = {
    'user': user,
    'status': 'draft',  # Clear what status is set
    'starting_price': Decimal('0.00'),  # Clear what price is set
    # ... all other defaults
}
```

### Clear Validation
```python
# Required fields are explicit
bio = serializers.CharField(required=True, max_length=500)
current_position = serializers.CharField(required=True, max_length=200)
industry = serializers.CharField(required=True, max_length=100)
```

### No Silent Failures
- All defaults are set explicitly in `create()` method
- No reliance on model defaults that could change
- Clear error messages for validation failures

---

## Maintenance Notes

### For Backend Engineers

**When adding new profile fields**:
1. Determine if field should be user-editable or system-managed
2. If user-editable: Add to `MentorProfileCreateSerializer.Meta.fields`
3. If system-managed: Add to `create()` method with explicit default
4. Update this documentation

**Pattern for System Defaults**:
```python
def create(self, validated_data):
    profile_data = {
        'user': validated_data.pop('user'),
        'new_system_field': 'default_value',  # Add here
        # ... other defaults
    }
    profile_data.update(validated_data)
    return MentorProfile.objects.create(**profile_data)
```

---

## Related Documentation
- `MENTOR_PROFILE_CREATE_UPDATE_FIX.md` - Profile CREATE vs UPDATE separation
- `MENTOR_ONBOARDING_UX_FIX.md` - Frontend onboarding states
- `gateai/human_loop/models.py` - MentorProfile model definition

---

**Signed Off By**: GateAI Backend Team  
**Review Status**: ✅ APPROVED  
**Production Ready**: YES

---

## Key Takeaway

**This fix implements proper separation of concerns:**
- **User provides**: Business data (bio, position, industry)
- **System manages**: Infrastructure data (status, ratings, earnings, verification)

New profiles start in **"draft"** status with clean system defaults, ready for the mentor to complete onboarding.

