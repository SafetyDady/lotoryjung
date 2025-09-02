# Individual Number Limits Management System

## Overview

Individual Number Limits Management System เป็นระบบการจัดการขีดจำกัดเฉพาะเลขแต่ละตัว ที่อนุญาตให้ผู้ดูแลระบบสามารถกำหนดขีดจำกัดการแทงเฉพาะเลขใดเลขหนึ่งได้ โดยจะมีความสำคัญสูงกว่าขีดจำกัดเริ่มต้นของกลุ่ม

## System Architecture

### Database Schema

```sql
-- Rule table structure for individual limits
CREATE TABLE rule (
    id INTEGER PRIMARY KEY,
    rule_type VARCHAR(50),          -- 'number_limit' for individual
    field VARCHAR(20),              -- '2_top', '2_bottom', '3_top', 'tote'
    number_norm VARCHAR(10),        -- Normalized number (e.g., '01', '012')
    limit_amount DECIMAL(15,2),     -- Individual limit amount
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Validation Priority Logic

```
Priority 1: Check Blocked Numbers
    ├── If blocked → Return 0.5x payout rate
    └── If not blocked → Continue to Priority 2

Priority 2: Check Individual Limits
    ├── If individual limit exists → Use individual limit
    └── If no individual limit → Continue to Priority 3

Priority 3: Apply Default Group Limits
    └── Use default group limit for field type
```

## Core Features

### 1. CRUD Operations

#### Create Individual Limit
- **Route**: `POST /admin/api/set_individual_limit`
- **Parameters**: 
  - `field`: Field type (2_top, 2_bottom, 3_top, tote)
  - `number_norm`: Normalized number string
  - `limit_amount`: Decimal limit amount
- **Authentication**: Admin required + CSRF protection

#### Read Individual Limits
- **Route**: `GET /admin/individual_limits`
- **Features**:
  - Display all individual limits in table format
  - Show current usage vs limit
  - Progress bars with color coding
  - Filter by field type and search by number

#### Update Individual Limit
- **Method**: Same as Create (upsert operation)
- **UI**: Bootstrap modal with pre-filled values

#### Delete Individual Limit
- **Route**: `POST /admin/api/delete_individual_limit`
- **Action**: Sets `is_active = false` (soft delete)

### 2. User Interface Components

#### Main Dashboard
```html
<!-- Default Limits Summary Card -->
<div class="card border-info">
    <div class="card-header bg-info text-white">
        <h5>ขีดจำกัดเริ่มต้น (Default Limits)</h5>
    </div>
    <div class="card-body">
        <!-- Display current default limits -->
    </div>
</div>

<!-- Individual Limits Table -->
<div class="card">
    <div class="card-header">
        <h5>รายการขีดจำกัดเฉพาะเลข</h5>
    </div>
    <div class="card-body">
        <!-- Filterable table with CRUD actions -->
    </div>
</div>
```

#### Action Modals
- **Add Limit Modal**: Form to create new individual limit
- **Edit Limit Modal**: Form to modify existing limit
- **Delete Confirmation**: Confirmation dialog for deletion

### 3. Security Implementation

#### CSRF Protection
All AJAX requests include CSRF token in headers:
```javascript
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': '{{ csrf_token() }}'
}
```

#### Authentication & Authorization
- `@login_required`: Ensures user is authenticated
- `@admin_required`: Ensures user has admin privileges

## Service Layer Architecture

### LimitService Class Methods

#### Core Individual Limits Methods
```python
@staticmethod
def get_individual_limit(field: str, number_norm: str) -> Optional[Decimal]:
    """Get individual limit for specific number"""

@staticmethod
def set_individual_limit(field: str, number_norm: str, limit_amount: Decimal) -> bool:
    """Set/update individual limit (upsert operation)"""

@staticmethod
def get_individual_limits_list(field: str = None) -> List[Dict]:
    """Get list of all individual limits with metadata"""

@staticmethod
def validate_order_item(field: str, number_norm: str, buy_amount: Decimal, batch_id: str = None) -> Dict:
    """Comprehensive validation with priority logic"""
```

#### Validation Logic Flow
```python
def validate_order_item(field, number_norm, buy_amount, batch_id=None):
    # Step 1: Check if number is blocked
    if is_blocked_number(field, number_norm):
        return {
            'is_valid': True,
            'payout_rate': 0.5,
            'reason': 'เลขอั้น - จ่ายครึ่งเท่า'
        }
    
    # Step 2: Get applicable limit (individual or default)
    individual_limit = get_individual_limit(field, number_norm)
    limit = individual_limit if individual_limit else get_default_group_limit(field)
    
    # Step 3: Check current usage
    current_usage = get_current_usage(field, number_norm, batch_id)
    
    # Step 4: Validate against limit
    if current_usage + buy_amount > limit:
        return {
            'is_valid': True,
            'payout_rate': 0.5,
            'reason': 'เกินขีดจำกัด - จ่ายครึ่งเท่า'
        }
    
    return {
        'is_valid': True,
        'payout_rate': 1.0,
        'reason': 'ปกติ'
    }
```

## Frontend Implementation

### JavaScript Functionality

#### Form Handling
```javascript
// Add Individual Limit
document.getElementById('addLimitForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const data = {
        field: formData.get('field'),
        number_norm: formData.get('number_norm'),
        limit_amount: parseFloat(formData.get('limit_amount'))
    };
    
    fetch('/admin/api/set_individual_limit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify(data)
    });
});
```

#### Filter and Search
- Field type filter dropdown
- Number search input
- Limit amount range filter
- Real-time table filtering

### UI Components

#### Progress Bars
```html
{% set usage = limit.get('current_usage', 0) %}
{% set percent = (usage / limit.limit * 100) if limit.limit > 0 else 0 %}
{% set display_percent = percent if percent <= 100 else 100 %}

<div class="progress">
    <div class="progress-bar 
        {% if percent >= 100 %}bg-danger
        {% elif percent >= 75 %}bg-warning
        {% elif percent >= 50 %}bg-info
        {% else %}bg-success{% endif %}"
        style="width: {{ display_percent }}%">
    </div>
</div>
```

## Integration Points

### 1. Order Processing Integration
When users submit orders, the validation flow automatically:
1. Checks blocked numbers first
2. Applies individual limits if they exist
3. Falls back to default group limits
4. Calculates appropriate payout rates

### 2. Admin Dashboard Integration
- Navigation menu includes "ขีดจำกัดเลขแต่ละตัว" link
- Seamless switching between group and individual limit management
- Unified admin interface design

### 3. Reporting Integration
Individual limits usage is tracked and can be included in:
- Daily usage reports
- Limit analysis reports
- Performance monitoring

## Configuration and Deployment

### Environment Requirements
- Flask application with SQLAlchemy
- Bootstrap 5.3.0 for UI components
- Font Awesome for icons
- jQuery for AJAX functionality

### Database Migration
```sql
-- Ensure rule table has proper structure
ALTER TABLE rule ADD COLUMN IF NOT EXISTS rule_type VARCHAR(50);
UPDATE rule SET rule_type = 'number_limit' WHERE rule_type IS NULL AND number_norm IS NOT NULL;
UPDATE rule SET rule_type = 'default_limit' WHERE rule_type IS NULL AND number_norm IS NULL;
```

## Troubleshooting

### Common Issues

#### CSRF Token Errors (HTTP 400)
**Problem**: AJAX requests failing with 400 status
**Solution**: Ensure all fetch requests include CSRF token in headers

#### Template Rendering Errors
**Problem**: Jinja2 template functions not recognized
**Solution**: Use conditional expressions instead of Python functions:
```html
<!-- ❌ Wrong -->
style="width: {{ min(percent, 100) }}%"

<!-- ✅ Correct -->
{% set display_percent = percent if percent <= 100 else 100 %}
style="width: {{ display_percent }}%"
```

#### Route Redirect Issues
**Problem**: Individual limits page redirects to dashboard
**Solution**: Check server logs for Python exceptions in route handlers

### Debugging Tools
- Flask debug mode enabled for development
- Console logging in JavaScript
- Server-side debug prints in route handlers
- Database query logging

## API Reference

### Set Individual Limit
```http
POST /admin/api/set_individual_limit
Content-Type: application/json
X-CSRFToken: <token>

{
    "field": "2_top",
    "number_norm": "12",
    "limit_amount": 500
}
```

### Delete Individual Limit
```http
POST /admin/api/delete_individual_limit
Content-Type: application/json
X-CSRFToken: <token>

{
    "field": "2_top",
    "number_norm": "12"
}
```

### Response Format
```json
{
    "success": true,
    "message": "กำหนดขีดจำกัดสำหรับเลข 12 เรียบร้อยแล้ว"
}
```

## Future Enhancements

1. **Bulk Individual Limits**: Upload CSV file to set multiple individual limits
2. **Time-based Limits**: Individual limits that change based on time periods
3. **Automatic Limit Adjustment**: AI-based limit recommendations
4. **Advanced Analytics**: Individual limit effectiveness analysis
5. **Mobile Interface**: Responsive design improvements for mobile admin access

## Conclusion

Individual Number Limits Management System provides granular control over lottery number betting limits, enhancing the flexibility and control of the lottery management system while maintaining security and user experience standards.
