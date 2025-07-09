# New Storage System - PostgreSQL Implementation

## Overview
A new storage system has been implemented for the grade-phoenix-bot using PostgreSQL on Railway. The system stores user data and grades with automatic change detection and comparison functionality.

## Database Schema

### Users Table
- **Primary Key**: `username` (String, 100 chars)
- **Unique Constraint**: `telegram_id` (Integer)
- **Fields**:
  - `fullname`, `firstname`, `lastname`, `email` (String)
  - `session_token` (Text) - for API authentication
  - `token_expires_at` (DateTime) - token expiration
  - `last_login` (DateTime) - last login timestamp
  - `is_active` (Boolean) - user status
  - `created_at`, `updated_at` (DateTime) - timestamps

### Grades Table
- **Primary Key**: `id` (Auto-increment Integer)
- **Foreign Key**: `username` → `users.username` (CASCADE delete)
- **Fields**:
  - `name` (String, 200 chars) - Course name
  - `code` (String, 50 chars) - Course code
  - `coursework`, `final_exam`, `total` (String, 50 chars) - Grade values
  - `ects` (Float) - ECTS credits
  - `term_name`, `term_id` (String) - Term information
  - `grade_status` (String, 50 chars) - Published/Not Published/Unknown
  - `numeric_grade` (Float) - Extracted numeric value
  - `created_at`, `updated_at` (DateTime) - timestamps

## Key Features

### 1. **Primary Key: Username**
- Users are identified by their university username
- Ensures unique identification across the system
- Telegram ID is unique but not primary key

### 2. **Grade Change Detection**
- Automatic comparison when grades are fetched
- Detects changes in coursework, final exam, and total grades
- Provides detailed change notifications
- Stores change history for tracking

### 3. **PostgreSQL on Railway**
- Uses `$DATABASE_URL` environment variable
- Automatic table creation and migration
- Connection pooling and optimization
- Timezone-aware timestamps

### 4. **Storage Components**

#### UserStorageV2
- User CRUD operations
- Session token management
- User search and statistics
- Expired token detection

#### GradeStorageV2
- Grade storage and retrieval
- Change detection and comparison
- Term-based grade organization
- GPA calculation support

#### DatabaseManager
- Connection management
- Session handling
- Table creation and testing
- Migration support

## Usage Examples

### User Registration
```python
user_data = {
    'username': 'student123',
    'telegram_id': 123456789,
    'fullname': 'John Doe',
    'email': 'john@university.edu'
}
success = user_storage.create_user(user_data)
```

### Grade Storage and Comparison
```python
# Store new grades
grades_data = [
    {
        'name': 'Advanced Mathematics',
        'code': 'MATH101',
        'coursework': '85 %',
        'final_exam': '90 %',
        'total': '87 %',
        'ects': 3.0,
        'term_name': 'Fall 2024'
    }
]
success = grade_storage.store_grades('student123', grades_data)

# Compare grades for changes
changes = grade_storage.compare_grades('student123', new_grades)
for change in changes:
    print(f"Course: {change['course_name']}")
    print(f"Field: {change['field']}")
    print(f"Old: {change['old_value']} → New: {change['new_value']}")
```

### Grade Retrieval
```python
# Get current term grades
current_grades = grade_storage.get_current_term_grades('student123')

# Get old term grades
old_grades = grade_storage.get_old_term_grades('student123')

# Get specific term grades
term_grades = grade_storage.get_user_grades('student123', 'Fall 2024')
```

## Migration System

### Alembic Setup
- Initial migration: `001_initial_migration.py`
- Creates users and grades tables
- Adds performance indexes
- Supports rollback

### Running Migrations
```bash
# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check migration status
alembic current
```

## Environment Configuration

### Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/database
```

### Railway Deployment
1. Set `DATABASE_URL` in Railway environment
2. Deploy application
3. Run migrations: `alembic upgrade head`
4. Verify connection: Check logs for "Database connection test successful"

## Performance Optimizations

### Database Indexes
- `ix_grades_username` - Fast user grade lookups
- `ix_grades_code` - Fast course code searches
- `ix_grades_term_name` - Fast term-based queries

### Connection Pooling
- Pre-ping connections for reliability
- Connection recycling every 5 minutes
- Null pool for migration operations

## Error Handling

### Graceful Degradation
- Storage failures don't crash the bot
- Fallback to default values
- Comprehensive error logging
- User-friendly error messages

### Data Validation
- Input validation for all user data
- Grade format validation
- Duplicate user prevention
- Foreign key constraint enforcement

## Security Features

### Data Protection
- No password storage (as per design)
- Session token encryption
- Automatic token expiration
- User activity logging

### Access Control
- User isolation by username
- Cascade delete for data consistency
- Read-only operations where appropriate
- Admin-only bulk operations

## Monitoring and Maintenance

### Health Checks
```python
# Test database connection
db_manager.test_connection()

# Get user statistics
user_count = user_storage.get_user_count()
grade_stats = grade_storage.get_grade_statistics('username')
```

### Backup and Recovery
- Automatic table creation
- Migration-based schema updates
- Data export capabilities
- Rollback support

## Integration Points

### Bot Integration
- Automatic storage initialization
- Grade change notifications
- User session management
- Admin dashboard integration

### API Integration
- University API data storage
- Grade comparison on fetch
- Change detection and alerts
- Historical data preservation

## Future Enhancements

### Planned Features
- Grade analytics and trends
- Performance benchmarking
- Advanced search capabilities
- Data export/import tools
- Multi-term grade history
- GPA tracking over time

### Scalability Considerations
- Database connection pooling
- Index optimization
- Query performance monitoring
- Data archiving strategies
- Sharding for large datasets

## Troubleshooting

### Common Issues
1. **Connection Errors**: Check `DATABASE_URL` format
2. **Migration Failures**: Verify database permissions
3. **Performance Issues**: Check index usage
4. **Data Inconsistencies**: Run data validation

### Debug Commands
```bash
# Test database connection
python -c "from storage.models import DatabaseManager; DatabaseManager('$DATABASE_URL').test_connection()"

# Check migration status
alembic current

# View database schema
alembic show 001
```

## Support

For issues or questions about the storage system:
1. Check the logs for detailed error messages
2. Verify environment variables are set correctly
3. Test database connectivity
4. Review migration status
5. Contact the development team

---

**Note**: This storage system is designed to work seamlessly with the existing bot functionality while providing robust data persistence and change detection capabilities. 