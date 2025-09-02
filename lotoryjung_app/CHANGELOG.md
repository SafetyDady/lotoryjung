# Changelog

All notable changes to the Lotoryjung project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-02

### 🎉 Major Features Added
- **Individual Number Limits Management System**
  - Complete CRUD operations for number-specific limits
  - Priority-based validation logic (Blocked → Individual → Group)
  - Advanced UI with Bootstrap modals and progress bars
  - Real-time usage tracking and visual indicators

### 🔧 Backend Enhancements
- **Extended LimitService Class**
  - `get_individual_limit()` - Retrieve specific number limits
  - `set_individual_limit()` - Create/update individual limits
  - `get_individual_limits_list()` - List all individual limits
  - Enhanced `validate_order_item()` with priority logic

- **Database Schema Updates**
  - Extended `rule` table with `rule_type` field
  - Support for both 'default_limit' and 'number_limit' types
  - Proper indexing for performance optimization

### 🎨 Frontend Improvements
- **Individual Limits Management Page**
  - Complete dashboard with filtering and search
  - Modal-based forms for add/edit operations
  - Color-coded progress bars for usage visualization
  - Responsive design with Bootstrap 5.3.0

- **Enhanced Admin Navigation**
  - Updated sidebar with Individual Limits link
  - Consistent design across all admin pages
  - Improved user experience with visual feedback

### 🛡️ Security Enhancements
- **CSRF Protection Implementation**
  - Added CSRF tokens to all AJAX requests
  - Fixed HTTP 400 errors in API endpoints
  - Enhanced form security across the application

### 🐛 Bug Fixes
- **Template Rendering Issues**
  - Fixed Jinja2 `min()` function compatibility
  - Resolved template inheritance problems
  - Corrected JavaScript validation errors

- **API Endpoint Fixes**
  - Fixed redirect issues in individual_limits route
  - Enhanced error handling with detailed logging
  - Improved response format consistency

### 📚 Documentation Updates
- **New Documentation Files**
  - `INDIVIDUAL_LIMITS_DESIGN.md` - Complete system design
  - `API_DOCUMENTATION.md` - Comprehensive API reference
  - Updated `README.md` with new features
  - Enhanced `STRUCTURE.md` with current architecture

### 🔄 API Changes
- **New Endpoints**
  - `POST /admin/api/set_individual_limit` - Manage individual limits
  - `POST /admin/api/delete_individual_limit` - Remove individual limits
  - Enhanced validation responses with priority information

### ⚡ Performance Improvements
- **Database Optimization**
  - Added strategic indexes for faster queries
  - Optimized limit lookup operations
  - Improved batch processing efficiency

### 🧪 Testing & Validation
- **Comprehensive Testing**
  - Individual limits CRUD operations validated
  - Priority validation logic confirmed working
  - Security features tested and verified
  - UI responsiveness across different devices

---

## [1.5.0] - 2025-09-01

### ✨ Features Added
- **Group Limits Management System**
  - Default limits configuration for all field types
  - Real-time usage monitoring and visualization
  - Dashboard with progress indicators
  - API endpoints for limit management

### 🔧 Backend Changes
- **LimitService Implementation**
  - Core business logic for limits management
  - Validation engine with configurable rules
  - Usage calculation and reporting
  - Integration with order processing

### 🎨 UI/UX Improvements
- **Admin Dashboard Enhancement**
  - Statistics overview with visual cards
  - Quick access buttons for common operations
  - Responsive design improvements
  - Enhanced navigation structure

### 📊 Data Management
- **Enhanced Database Schema**
  - `rule` table for limits configuration
  - `number_total` table for usage tracking
  - `audit_log` table for change tracking
  - Improved relationships and constraints

---

## [1.0.0] - 2025-08-30

### 🎉 Initial Release
- **Core Application Framework**
  - Flask application with SQLAlchemy ORM
  - User authentication and authorization
  - Admin panel foundation
  - Basic security implementations

### 🚫 Blocked Numbers Management
- **Bulk Operations**
  - Auto-detection by number length
  - Permutation generation for all field types
  - Mass add/edit/delete operations
  - Search and filtering capabilities

### 🎨 User Interface
- **Bootstrap-based Design**
  - Responsive admin interface
  - Modern UI components
  - Form validation and feedback
  - Progressive enhancement with JavaScript

### 🔒 Security Features
- **Authentication System**
  - User login/logout functionality
  - Admin role-based access control
  - Session management
  - Password hashing

### 📊 Database Foundation
- **Core Models**
  - User management
  - Order and OrderItem tracking
  - BlockedNumber storage
  - Audit logging system

---

## Development Milestones

### Phase 1: Foundation (August 2025)
- ✅ Project setup and structure
- ✅ Database design and models
- ✅ Basic Flask application
- ✅ Initial admin interface

### Phase 2: Blocked Numbers (Early September 2025)
- ✅ Bulk operations interface
- ✅ Auto-detection system
- ✅ Permutation algorithms
- ✅ Search and filtering

### Phase 3: Group Limits (September 1, 2025)
- ✅ Limits configuration system
- ✅ Usage tracking and monitoring
- ✅ Validation engine
- ✅ Dashboard implementation

### Phase 4: Individual Limits (September 2, 2025)
- ✅ Granular number-specific limits
- ✅ Priority-based validation
- ✅ Advanced UI components
- ✅ Complete CRUD operations

### Phase 5: Documentation & Polish (September 2, 2025)
- ✅ Comprehensive documentation
- ✅ API reference guide
- ✅ Installation instructions
- ✅ System architecture documentation

---

## Breaking Changes

### Version 2.0.0
- **Database Schema Changes**
  - `rule` table structure extended with `rule_type` field
  - Migration required for existing installations
  - New indexes added for performance

- **API Response Format Changes**
  - Enhanced validation responses with priority information
  - Additional fields in limit management APIs
  - Improved error message format

### Migration Guide 1.x → 2.x
```sql
-- Add rule_type column to existing rule table
ALTER TABLE rule ADD COLUMN rule_type VARCHAR(50);

-- Update existing records
UPDATE rule SET rule_type = 'default_limit' WHERE number_norm IS NULL;
UPDATE rule SET rule_type = 'number_limit' WHERE number_norm IS NOT NULL;

-- Add new indexes
CREATE INDEX idx_rule_type_field ON rule(rule_type, field);
CREATE INDEX idx_rule_number_limit ON rule(rule_type, field, number_norm) 
WHERE rule_type = 'number_limit';
```

---

## Security Updates

### Version 2.0.0
- **CSRF Protection Enhanced**
  - All AJAX endpoints now require CSRF tokens
  - Form submission security improved
  - API endpoint authentication strengthened

### Version 1.5.0
- **Input Validation**
  - Enhanced server-side validation
  - XSS protection improvements
  - SQL injection prevention

### Version 1.0.0
- **Foundation Security**
  - User authentication system
  - Admin authorization checks
  - Password hashing implementation

---

## Known Issues

### Current Version (2.0.0)
- None known

### Previous Versions
- **v1.5.0**: Template rendering issues with certain Jinja2 functions (Fixed in v2.0.0)
- **v1.0.0**: CSRF token handling in AJAX requests (Fixed in v2.0.0)

---

## Deprecations

### Version 2.0.0
- No deprecations

### Future Considerations
- Legacy API endpoints may be deprecated in v3.0.0
- Old template structure may be updated in future releases

---

## Contributors

### Core Development Team
- **SafetyDady** - Project Lead & Core Developer
- **AI Assistant** - Technical Documentation & Code Review

### Special Thanks
- Bootstrap team for UI framework
- Flask community for excellent documentation
- SQLAlchemy team for powerful ORM

---

*Changelog maintained according to [Keep a Changelog](https://keepachangelog.com/) format*
*Last updated: September 2, 2025*
