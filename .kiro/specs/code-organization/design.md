# Design Document

## Overview

This design document outlines the refactoring of the Event Management API from a monolithic single-file structure to a well-organized, layered architecture. The refactoring will separate concerns into distinct layers (handlers, services, repositories) and organize code by domain (events, users, registrations). The design ensures all existing API functionality remains intact while improving maintainability, testability, and extensibility.

## Architecture

### Layered Architecture

The system will follow a three-layer architecture:

```
┌─────────────────────────────────────┐
│     API Layer (Handlers/Routes)     │  ← HTTP concerns, request/response
├─────────────────────────────────────┤
│     Service Layer (Business Logic)  │  ← Business rules, workflows
├─────────────────────────────────────┤
│     Repository Layer (Data Access)  │  ← Database operations
└─────────────────────────────────────┘
                  ↓
            DynamoDB Tables
```

### Directory Structure

```
backend/
├── main.py                          # FastAPI app initialization, middleware, routers
├── config.py                        # Configuration and environment variables
├── exceptions.py                    # Custom domain exceptions
├── dependencies.py                  # FastAPI dependency injection
├── domains/
│   ├── __init__.py
│   ├── events/
│   │   ├── __init__.py
│   │   ├── models.py               # Pydantic models for events
│   │   ├── repository.py           # Event data access
│   │   ├── service.py              # Event business logic
│   │   └── routes.py               # Event API handlers
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py               # Pydantic models for users
│   │   ├── repository.py           # User data access
│   │   ├── service.py              # User business logic
│   │   └── routes.py               # User API handlers
│   └── registrations/
│       ├── __init__.py
│       ├── models.py               # Pydantic models for registrations
│       ├── repository.py           # Registration data access
│       ├── service.py              # Registration business logic
│       └── routes.py               # Registration API handlers
├── requirements.txt
└── test_main.py                    # Integration tests
```

## Components and Interfaces

### Configuration Module (`config.py`)

Centralizes all configuration and environment variable access.

```python
class Config:
    DYNAMODB_TABLE: str
    USERS_TABLE: str
    REGISTRATIONS_TABLE: str
    ALLOWED_ORIGINS: List[str]
    AWS_REGION: str
    
    @classmethod
    def from_env(cls) -> Config
```

### Exception Module (`exceptions.py`)

Defines domain-specific exceptions that are raised by services and repositories.

```python
class DomainException(Exception)
class NotFoundException(DomainException)
class AlreadyExistsException(DomainException)
class ValidationException(DomainException)
class CapacityException(DomainException)
```

### Repository Layer

Each repository encapsulates all database operations for a domain.

**EventRepository Interface:**
```python
class EventRepository:
    def create(event_data: dict) -> dict
    def get_by_id(event_id: str) -> Optional[dict]
    def list_all() -> List[dict]
    def update(event_id: str, updates: dict) -> dict
    def delete(event_id: str) -> None
    def increment_counts(event_id: str, registered_delta: int, waitlist_delta: int) -> None
```

**UserRepository Interface:**
```python
class UserRepository:
    def create(user_data: dict) -> dict
    def get_by_id(user_id: str) -> Optional[dict]
```

**RegistrationRepository Interface:**
```python
class RegistrationRepository:
    def create(registration_data: dict) -> dict
    def get_by_event_and_user(event_id: str, user_id: str) -> Optional[dict]
    def list_by_event(event_id: str) -> List[dict]
    def list_by_user(user_id: str) -> List[dict]
    def delete(event_id: str, user_id: str) -> None
    def update_status(event_id: str, user_id: str, status: str, waitlist_position: Optional[int]) -> dict
    def get_waitlisted_users(event_id: str) -> List[dict]
```

### Service Layer

Services contain business logic and orchestrate between repositories.

**EventService Interface:**
```python
class EventService:
    def create_event(event: Event) -> dict
    def get_event(event_id: str) -> dict
    def list_events() -> List[dict]
    def update_event(event_id: str, updates: EventUpdate) -> dict
    def delete_event(event_id: str) -> dict
    def configure_waitlist(event_id: str, enabled: bool) -> dict
```

**UserService Interface:**
```python
class UserService:
    def create_user(user: UserCreate) -> dict
    def get_user(user_id: str) -> dict
    def get_user_registrations(user_id: str) -> List[dict]
```

**RegistrationService Interface:**
```python
class RegistrationService:
    def register_user(event_id: str, user_id: str) -> dict
    def unregister_user(event_id: str, user_id: str) -> dict
    def get_event_registrations(event_id: str) -> dict
```

### API Layer (Routes)

Each domain has a router module with FastAPI route handlers.

**Event Routes:**
- POST /events
- GET /events
- GET /events/{event_id}
- PUT /events/{event_id}
- DELETE /events/{event_id}
- PUT /events/{event_id}/waitlist

**User Routes:**
- POST /users
- GET /users/{user_id}
- GET /users/{user_id}/registrations

**Registration Routes:**
- POST /events/{event_id}/registrations
- GET /events/{event_id}/registrations
- DELETE /events/{event_id}/registrations/{user_id}

## Data Models

### Event Models

```python
class Event(BaseModel):
    eventId: Optional[str]
    title: str
    description: str
    date: str
    location: str
    capacity: int
    organizer: str
    status: str = "active"
    waitlistEnabled: bool = False
    registeredCount: int = 0
    waitlistCount: int = 0

class EventUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    date: Optional[str]
    location: Optional[str]
    capacity: Optional[int]
    organizer: Optional[str]
    status: Optional[str]
    waitlistEnabled: Optional[bool]
    registeredCount: Optional[int]
    waitlistCount: Optional[int]

class WaitlistConfig(BaseModel):
    waitlistEnabled: bool
```

### User Models

```python
class UserCreate(BaseModel):
    userId: Optional[str]
    name: str

class User(BaseModel):
    userId: str
    name: str
    createdAt: str
```

### Registration Models

```python
class RegistrationRequest(BaseModel):
    userId: str

class Registration(BaseModel):
    eventId: str
    userId: str
    status: str
    waitlistPosition: Optional[int]
    registeredAt: str

class UserRegistration(BaseModel):
    eventId: str
    eventTitle: str
    eventDate: str
    status: str
    waitlistPosition: Optional[int]
    registeredAt: str
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Validation failures raise domain exceptions

*For any* invalid input to a service method, the system should raise a domain-specific exception (ValidationException, NotFoundException, etc.) rather than allowing the error to propagate as a generic exception or returning an error value.

**Validates: Requirements 1.4**

### Property 2: Repository methods return domain types

*For any* repository method call that succeeds, the return value should be a dictionary, list, or primitive type representing domain data, never a DynamoDB response object (which would contain ResponseMetadata or other AWS-specific fields).

**Validates: Requirements 2.5**

### Property 3: Database errors translate to domain exceptions

*For any* simulated database error in a repository method, the system should catch the DynamoDB exception and raise a corresponding domain exception with appropriate context.

**Validates: Requirements 2.4**

### Property 4: API responses maintain backward compatibility

*For any* valid API request to a refactored endpoint, the response structure (field names, types, nesting) and status code should match the original implementation's response for the same request.

**Validates: Requirements 4.2**

### Property 5: Error responses maintain backward compatibility

*For any* invalid API request that triggers validation errors, the error response structure and status code should match the original implementation's error response for the same invalid request.

**Validates: Requirements 4.3**

### Property 6: Data consistency is preserved

*For any* sequence of valid operations (create, update, delete), the final state of the data should be consistent with the business rules (e.g., registeredCount matches actual registrations, waitlist positions are sequential).

**Validates: Requirements 4.4**

### Property 7: Repository exceptions are domain exceptions

*For any* error condition in a repository method (item not found, client error, etc.), the raised exception should be a subclass of DomainException, not a boto3 or botocore exception.

**Validates: Requirements 8.2**

### Property 8: Service exceptions propagate correctly

*For any* domain exception raised by a repository, when called through a service method, the exception should propagate to the caller without being caught or transformed by the service layer.

**Validates: Requirements 8.3**

### Property 9: Handlers translate exceptions to HTTP responses

*For any* domain exception caught by an API handler, the handler should return an HTTP response with a status code that correctly maps to the exception type (404 for NotFoundException, 409 for AlreadyExistsException, 422 for ValidationException, 500 for others).

**Validates: Requirements 8.4**

### Property 10: Errors are logged with context

*For any* error that occurs in any layer, the system should log the error with contextual information including the operation being performed, relevant entity IDs, and error details.

**Validates: Requirements 8.5**

## Error Handling

### Exception Hierarchy

```python
class DomainException(Exception):
    """Base exception for all domain errors"""
    def __init__(self, message: str, context: dict = None)

class NotFoundException(DomainException):
    """Raised when a requested entity is not found"""
    
class AlreadyExistsException(DomainException):
    """Raised when attempting to create an entity that already exists"""
    
class ValidationException(DomainException):
    """Raised when input validation fails"""
    
class CapacityException(DomainException):
    """Raised when an event is at capacity and waitlist is disabled"""
```

### Exception Translation

**Repository Layer:**
- Catches `ClientError` from boto3
- Translates to domain exceptions based on error code
- Includes relevant context (table name, key, operation)

**Service Layer:**
- Raises domain exceptions for business rule violations
- Propagates repository exceptions unchanged
- Adds business context to exceptions

**Handler Layer:**
- Catches domain exceptions
- Translates to HTTP responses with appropriate status codes:
  - `NotFoundException` → 404
  - `AlreadyExistsException` → 409
  - `ValidationException` → 422
  - `CapacityException` → 409
  - `DomainException` → 500
- Returns consistent error response format: `{"detail": "error message"}`

### Logging Strategy

All layers log at appropriate levels:
- INFO: Successful operations with entity IDs
- WARNING: Business rule violations, not found errors
- ERROR: Database errors, unexpected exceptions

Log format includes:
- Timestamp
- Log level
- Module/function name
- Operation description
- Entity IDs
- Error details (for errors)

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

**Repository Tests:**
- Mock DynamoDB responses
- Verify correct query/scan/put/update/delete operations
- Test exception translation from boto3 errors to domain exceptions
- Verify return types are domain objects, not DynamoDB responses

**Service Tests:**
- Mock repository methods
- Verify business logic correctness
- Test validation rules
- Verify exception handling and propagation
- Test complex workflows (registration with waitlist promotion)

**Handler Tests:**
- Mock service methods
- Verify HTTP request parsing
- Verify HTTP response formatting
- Test exception-to-HTTP translation
- Verify status codes

### Property-Based Testing

Property-based tests will verify universal properties using the Hypothesis library for Python:

**Configuration:**
- Each property test will run a minimum of 100 iterations
- Tests will use Hypothesis strategies to generate random valid and invalid inputs
- Each test will be tagged with a comment referencing the design document property

**Test Tagging Format:**
```python
# Feature: code-organization, Property 1: Validation failures raise domain exceptions
```

**Property Tests:**

1. **Validation Exception Property**: Generate random invalid inputs (empty strings, out-of-range numbers, invalid dates) and verify service methods raise ValidationException

2. **Repository Return Type Property**: Call repository methods with random valid inputs and verify return values are dicts/lists/primitives without DynamoDB metadata

3. **Database Error Translation Property**: Simulate random DynamoDB errors and verify repositories raise domain exceptions

4. **API Response Compatibility Property**: Generate random valid requests and compare refactored API responses to original responses

5. **Error Response Compatibility Property**: Generate random invalid requests and compare error responses to original error responses

6. **Data Consistency Property**: Generate random sequences of operations and verify final state consistency (counts match reality)

7. **Repository Exception Type Property**: Trigger various error conditions and verify all raised exceptions are DomainException subclasses

8. **Service Exception Propagation Property**: Inject repository exceptions and verify they propagate through services unchanged

9. **Handler Exception Translation Property**: Generate random domain exceptions and verify handlers return correct HTTP status codes

10. **Error Logging Property**: Trigger random errors and verify log entries contain required context fields

### Integration Testing

Integration tests will verify end-to-end functionality:

- Use existing `test_main.py` tests without modification
- Verify all endpoints are accessible
- Test complete workflows (create event, register user, unregister, etc.)
- Verify database state after operations
- Test error scenarios with real HTTP requests

### Backward Compatibility Testing

- Run all existing integration tests against refactored code
- Compare API responses between original and refactored implementations
- Verify no breaking changes in request/response formats
- Test error responses match original behavior

## Implementation Notes

### Dependency Injection

Use FastAPI's dependency injection for repositories and services:

```python
def get_event_repository() -> EventRepository:
    return EventRepository(table=dynamodb.Table(config.DYNAMODB_TABLE))

def get_event_service(
    repo: EventRepository = Depends(get_event_repository)
) -> EventService:
    return EventService(repository=repo)

@router.post("/events")
def create_event(
    event: Event,
    service: EventService = Depends(get_event_service)
):
    return service.create_event(event)
```

### Migration Strategy

1. Create new directory structure
2. Extract models to domain model modules
3. Implement repository layer with tests
4. Implement service layer with tests
5. Refactor handlers to use services
6. Update main.py to use new routers
7. Run integration tests to verify compatibility
8. Remove old main.py code

### Backward Compatibility Guarantees

- All endpoint paths remain unchanged
- All request/response formats remain unchanged
- All status codes remain unchanged
- All error messages remain unchanged
- All validation rules remain unchanged
- Database schema remains unchanged
- Environment variables remain unchanged
