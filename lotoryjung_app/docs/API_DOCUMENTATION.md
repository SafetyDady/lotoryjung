# Lotoryjung API Documentation

## Overview

Lotoryjung API provides endpoints for managing lottery limits, blocked numbers, and order validation. All admin APIs require authentication and CSRF protection.

## Authentication

### Admin Authentication Required
```python
@login_required      # User must be logged in
@admin_required     # User must have admin privileges
```

### CSRF Protection
All POST requests must include CSRF token in headers:
```javascript
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': '{{ csrf_token() }}'
}
```

## Individual Limits Management APIs

### Set Individual Limit
Creates or updates an individual number limit.

**Endpoint**: `POST /admin/api/set_individual_limit`

**Request Headers**:
```
Content-Type: application/json
X-CSRFToken: <csrf_token>
```

**Request Body**:
```json
{
    "field": "2_top",
    "number_norm": "12",
    "limit_amount": 500
}
```

**Parameters**:
- `field` (string): Field type - `2_top`, `2_bottom`, `3_top`, `tote`
- `number_norm` (string): Normalized number (e.g., "01", "12", "123")
- `limit_amount` (number): Limit amount in currency units

**Response Success (200)**:
```json
{
    "success": true,
    "message": "กำหนดขีดจำกัดสำหรับเลข 12 เรียบร้อยแล้ว"
}
```

**Response Error (400/500)**:
```json
{
    "success": false,
    "error": "ข้อมูลไม่ครบถ้วน (field, number_norm, limit_amount)"
}
```

**Example Usage**:
```javascript
fetch('/admin/api/set_individual_limit', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
    },
    body: JSON.stringify({
        field: '2_top',
        number_norm: '12',
        limit_amount: 500
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Limit set successfully');
    }
});
```

---

### Delete Individual Limit
Removes an individual number limit (soft delete).

**Endpoint**: `POST /admin/api/delete_individual_limit`

**Request Headers**:
```
Content-Type: application/json
X-CSRFToken: <csrf_token>
```

**Request Body**:
```json
{
    "field": "2_top",
    "number_norm": "12"
}
```

**Parameters**:
- `field` (string): Field type
- `number_norm` (string): Normalized number

**Response Success (200)**:
```json
{
    "success": true,
    "message": "ลบขีดจำกัดเรียบร้อยแล้ว"
}
```

**Response Error (400/500)**:
```json
{
    "success": false,
    "error": "ไม่พบขีดจำกัดที่ต้องการลบ"
}
```

---

## Group Limits Management APIs

### Update Group Limit
Updates default group limit for a field type.

**Endpoint**: `POST /admin/api/update_group_limit`

**Request Body**:
```json
{
    "field": "2_top",
    "limit": 1000000
}
```

**Response Success (200)**:
```json
{
    "success": true,
    "message": "อัปเดตขีดจำกัดเริ่มต้นสำหรับ 2_top เรียบร้อยแล้ว"
}
```

---

### Get Dashboard Data
Retrieves current limits and usage statistics.

**Endpoint**: `GET /admin/group_limits/api/dashboard_data`

**Query Parameters**:
- `batch_id` (optional): Specific batch ID for usage calculation

**Response Success (200)**:
```json
{
    "success": true,
    "data": {
        "2_top": {
            "field_name": "2 ตัวบน",
            "limit_amount": 700.00,
            "used_amount": 150.00,
            "remaining_amount": 550.00,
            "usage_percent": 21.43,
            "order_count": 5,
            "number_count": 3,
            "status": "normal",
            "is_exceeded": false
        }
    }
}
```

---

### Validate Order
Validates order items against current limits.

**Endpoint**: `POST /admin/group_limits/api/validate_order`

**Request Body**:
```json
{
    "order_items": [
        {
            "field": "2_top",
            "number_norm": "12",
            "buy_amount": 300
        }
    ],
    "batch_id": "20250902"
}
```

**Response Success (200)**:
```json
{
    "success": true,
    "is_valid": true,
    "errors": [],
    "results": [
        {
            "is_valid": true,
            "payout_rate": 1.0,
            "reason": "ปกติ",
            "limit": 500.00,
            "current_usage": 200.00,
            "is_blocked": false
        }
    ]
}
```

---

## Validation Service APIs

The validation system uses a priority-based approach:

### Validation Priority Logic
1. **Blocked Numbers Check** (Priority 1)
   - If number is blocked → `payout_rate: 0.5`
   - If not blocked → Continue to step 2

2. **Individual Limits Check** (Priority 2)
   - If individual limit exists → Use individual limit
   - If no individual limit → Continue to step 3

3. **Group Limits Check** (Priority 3)
   - Apply default group limit for field type

### Validation Response Format
```json
{
    "is_valid": true,
    "payout_rate": 1.0,
    "reason": "ปกติ",
    "limit": 500.00,
    "current_usage": 200.00,
    "remaining_amount": 300.00,
    "is_blocked": false,
    "limit_type": "individual"
}
```

**Fields Explanation**:
- `is_valid`: Whether the order is acceptable
- `payout_rate`: Payout multiplier (1.0 = normal, 0.5 = reduced)
- `reason`: Human-readable reason in Thai
- `limit`: Applicable limit amount
- `current_usage`: Current usage against the limit
- `remaining_amount`: Remaining available amount
- `is_blocked`: Whether the number is in blocked list
- `limit_type`: Type of limit applied ("individual", "group", or "blocked")

## Error Handling

### Common HTTP Status Codes
- `200`: Success
- `400`: Bad Request (missing/invalid parameters)
- `401`: Unauthorized (not logged in)
- `403`: Forbidden (not admin)
- `404`: Not Found
- `500`: Internal Server Error

### Error Response Format
```json
{
    "success": false,
    "error": "Error message in Thai",
    "details": "Optional detailed error information"
}
```

### Common Errors

#### CSRF Token Missing (400)
```json
{
    "success": false,
    "error": "CSRF token missing or invalid"
}
```

#### Insufficient Privileges (403)
```json
{
    "success": false,
    "error": "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"
}
```

#### Invalid Field Type (400)
```json
{
    "success": false,
    "error": "Invalid field type. Must be one of: 2_top, 2_bottom, 3_top, tote"
}
```

#### Database Error (500)
```json
{
    "success": false,
    "error": "Database operation failed",
    "details": "Connection timeout or constraint violation"
}
```

## Rate Limiting

Default rate limits applied:
- 200 requests per day per IP
- 50 requests per hour per IP

For higher limits, contact system administrator.

## Testing Examples

### Python Testing
```python
import requests

# Set individual limit
response = requests.post(
    'http://127.0.0.1:8080/admin/api/set_individual_limit',
    json={
        'field': '2_top',
        'number_norm': '12',
        'limit_amount': 500
    },
    headers={'X-CSRFToken': 'your_csrf_token'},
    cookies={'session': 'your_session_cookie'}
)

print(response.json())
```

### cURL Testing
```bash
# Set individual limit
curl -X POST http://127.0.0.1:8080/admin/api/set_individual_limit \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your_csrf_token" \
  -b "session=your_session_cookie" \
  -d '{"field":"2_top","number_norm":"12","limit_amount":500}'

# Get dashboard data
curl -X GET "http://127.0.0.1:8080/admin/group_limits/api/dashboard_data?batch_id=20250902" \
  -b "session=your_session_cookie"
```

## SDK Examples

### JavaScript SDK Pattern
```javascript
class LotoryjungAPI {
    constructor(baseURL, csrfToken) {
        this.baseURL = baseURL;
        this.csrfToken = csrfToken;
    }

    async setIndividualLimit(field, numberNorm, limitAmount) {
        const response = await fetch(`${this.baseURL}/admin/api/set_individual_limit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                field: field,
                number_norm: numberNorm,
                limit_amount: limitAmount
            })
        });
        return response.json();
    }

    async validateOrder(orderItems, batchId = null) {
        const response = await fetch(`${this.baseURL}/admin/group_limits/api/validate_order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                order_items: orderItems,
                batch_id: batchId
            })
        });
        return response.json();
    }
}

// Usage
const api = new LotoryjungAPI('http://127.0.0.1:8080', document.querySelector('[name=csrf_token]').value);

// Set individual limit
api.setIndividualLimit('2_top', '12', 500)
    .then(result => console.log(result));

// Validate order
api.validateOrder([
    { field: '2_top', number_norm: '12', buy_amount: 300 }
], '20250902')
    .then(result => console.log(result));
```

## Version History

### v2.0 (September 2, 2025)
- Added Individual Limits Management APIs
- Enhanced validation with priority logic
- Improved error handling and responses
- Added comprehensive CSRF protection

### v1.0 (September 1, 2025)
- Initial API release
- Group limits management
- Basic validation endpoints
- Admin authentication system

---

*API Documentation v2.0 - Last Updated: September 2, 2025*
