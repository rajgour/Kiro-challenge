# Implementation Plan

- [ ] 1. Create project structure and shared modules
  - Create directory structure for domains (events, users, registrations)
  - Create `backend/config.py` for configuration management
  - Create `backend/exceptions.py` with domain exception classes
  - Create `backend/dependencies.py` for FastAPI dependency injection setup
  - _Requirements: 3.1, 3.2, 7.1, 8.1_

- [ ]* 1.1 Write property test for exception class hierarchy
  - **Property 7: Repository exceptions are domain exceptions**
  - **Validates: Requirements 8.2**

- [ ] 2. Extract and organize Pydantic models
  - Create `backend/domains/events/models.py` with Event, EventUpdate, WaitlistConfig models
  - Create `backend/domains/users/models.py` with User, UserCreate models
  - Create `backend/domains/registrations/models.py` with Registration, RegistrationRequest, UserRegistration models
  - Ensure all validation rules and field validators are preserved
  - _Requirements: 6.1, 6.2_

- [ ]* 2.1 Write unit tests for model validation
  - Test all Pydantic validators work correctly
  - Test field constraints (min_length, max_length, etc.)
  - _Requirements: 6.2_

- [ ] 3. Implement repository layer for events
  - Create `backend/domains/events/repository.py` with EventRepository class
  - Implement create, get_by_id, list_all, update, delete methods
  - Implement increment_counts method for registration count updates
  - Translate DynamoDB ClientError exceptions to domain exceptions
  - Ensure methods return domain objects, not raw DynamoDB responses
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ]* 3.1 Write property test for repository return types
  - **Property 2: Repository methods return domain types**
  - **Validates: Requirements 2.5**

- [ ]* 3.2 Write property test for database error translation
  - **Property 3: Database errors translate to domain exceptions**
  - **Validates: Requirements 2.4**

- [ ]* 3.3 Write unit tests for event repository
  - Test CRUD operations with mocked DynamoDB
  - Test error handling and exception translation
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 4. Implement repository layer for users
  - Create `backend/domains/users/repository.py` with UserRepository class
  - Implement create and get_by_id methods
  - Translate DynamoDB exceptions to domain exceptions
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ]* 4.1 Write unit tests for user repository
  - Test create and get operations with mocked DynamoDB
  - Test error handling
  - _Requirements: 2.1, 2.2_

- [ ] 5. Implement repository layer for registrations
  - Create `backend/domains/registrations/repository.py` with RegistrationRepository class
  - Implement create, get_by_event_and_user, list_by_event, list_by_user methods
  - Implement delete, update_status, get_waitlisted_users methods
  - Translate DynamoDB exceptions to domain exceptions
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ]* 5.1 Write unit tests for registration repository
  - Test all CRUD operations with mocked DynamoDB
  - Test query operations (by event, by user)
  - Test error handling
  - _Requirements: 2.1, 2.2_

- [ ] 6. Implement service layer for events
  - Create `backend/domains/events/service.py` with EventService class
  - Implement create_event, get_event, list_events methods
  - Implement update_event, delete_event, configure_waitlist methods
  - Add business logic validation (status validation, etc.)
  - Raise domain exceptions for business rule violations
  - _Requirements: 1.1, 1.3, 1.4, 2.3_

- [ ]* 6.1 Write property test for validation exceptions
  - **Property 1: Validation failures raise domain exceptions**
  - **Validates: Requirements 1.4**

- [ ]* 6.2 Write unit tests for event service
  - Test business logic with mocked repository
  - Test validation rules
  - Test exception handling
  - _Requirements: 1.1, 1.3_

- [ ] 7. Implement service layer for users
  - Create `backend/domains/users/service.py` with UserService class
  - Implement create_user, get_user, get_user_registrations methods
  - Add business logic for user creation (generate UUID if not provided)
  - Enrich user registrations with event details
  - _Requirements: 1.1, 1.3, 1.4, 2.3_

- [ ]* 7.1 Write unit tests for user service
  - Test user creation logic
  - Test registration enrichment
  - Test error handling
  - _Requirements: 1.1, 1.3_

- [ ] 8. Implement service layer for registrations
  - Create `backend/domains/registrations/service.py` with RegistrationService class
  - Implement register_user method with capacity and waitlist logic
  - Implement unregister_user method with waitlist promotion logic
  - Implement get_event_registrations method
  - Add business logic for registration status determination
  - _Requirements: 1.1, 1.3, 1.4, 2.3_

- [ ]* 8.1 Write property test for data consistency
  - **Property 6: Data consistency is preserved**
  - **Validates: Requirements 4.4**

- [ ]* 8.2 Write unit tests for registration service
  - Test registration logic (capacity, waitlist)
  - Test unregistration logic (waitlist promotion)
  - Test complex workflows
  - _Requirements: 1.1, 1.3_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement API routes for events
  - Create `backend/domains/events/routes.py` with FastAPI router
  - Implement POST /events, GET /events, GET /events/{event_id}
  - Implement PUT /events/{event_id}, DELETE /events/{event_id}
  - Implement PUT /events/{event_id}/waitlist
  - Use dependency injection for EventService
  - Translate domain exceptions to HTTP responses
  - _Requirements: 1.2, 3.4, 8.4_

- [ ]* 10.1 Write property test for exception-to-HTTP translation
  - **Property 9: Handlers translate exceptions to HTTP responses**
  - **Validates: Requirements 8.4**

- [ ]* 10.2 Write unit tests for event routes
  - Test request parsing and response formatting
  - Test exception handling
  - Test status codes
  - _Requirements: 1.2, 8.4_

- [ ] 11. Implement API routes for users
  - Create `backend/domains/users/routes.py` with FastAPI router
  - Implement POST /users, GET /users/{user_id}
  - Implement GET /users/{user_id}/registrations
  - Use dependency injection for UserService
  - Translate domain exceptions to HTTP responses
  - _Requirements: 1.2, 3.4, 8.4_

- [ ]* 11.1 Write unit tests for user routes
  - Test request parsing and response formatting
  - Test exception handling
  - _Requirements: 1.2, 8.4_

- [ ] 12. Implement API routes for registrations
  - Create `backend/domains/registrations/routes.py` with FastAPI router
  - Implement POST /events/{event_id}/registrations
  - Implement GET /events/{event_id}/registrations
  - Implement DELETE /events/{event_id}/registrations/{user_id}
  - Use dependency injection for RegistrationService
  - Translate domain exceptions to HTTP responses
  - _Requirements: 1.2, 3.4, 8.4_

- [ ]* 12.1 Write unit tests for registration routes
  - Test request parsing and response formatting
  - Test exception handling
  - _Requirements: 1.2, 8.4_

- [ ] 13. Refactor main application file
  - Update `backend/main.py` to import and register all domain routers
  - Keep FastAPI app initialization, middleware, and CORS configuration
  - Add exception handlers for domain exceptions
  - Remove old route handlers and business logic
  - Keep health check and root endpoints
  - _Requirements: 3.5, 7.3, 8.4_

- [ ]* 13.1 Write property test for error logging
  - **Property 10: Errors are logged with context**
  - **Validates: Requirements 8.5**

- [ ] 14. Implement configuration module
  - Create `backend/config.py` with Config class
  - Load all environment variables (table names, CORS origins, region)
  - Add validation for required configuration
  - _Requirements: 7.1, 7.5_

- [ ] 15. Implement dependency injection
  - Create `backend/dependencies.py` with dependency functions
  - Implement get_event_repository, get_user_repository, get_registration_repository
  - Implement get_event_service, get_user_service, get_registration_service
  - Use FastAPI Depends for injection
  - _Requirements: 5.3, 7.4_

- [ ] 16. Add exception handlers to main app
  - Register exception handlers for all domain exception types
  - Map NotFoundException to 404
  - Map AlreadyExistsException to 409
  - Map ValidationException to 422
  - Map CapacityException to 409
  - Map generic DomainException to 500
  - Ensure error response format matches original: {"detail": "message"}
  - _Requirements: 8.4_

- [ ] 17. Checkpoint - Run integration tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 18. Write property test for API response compatibility
  - **Property 4: API responses maintain backward compatibility**
  - **Validates: Requirements 4.2**

- [ ]* 18.1 Write property test for error response compatibility
  - **Property 5: Error responses maintain backward compatibility**
  - **Validates: Requirements 4.3**

- [ ]* 19. Write integration tests for backward compatibility
  - Test all endpoints return expected response structures
  - Test all error cases return expected error responses
  - Compare with original implementation behavior
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ] 20. Update lambda handler
  - Ensure `backend/lambda_package/lambda_handler.py` imports from refactored main.py
  - Verify Mangum handler still works correctly
  - Test Lambda deployment compatibility
  - _Requirements: 4.1_

- [ ] 21. Final checkpoint - Verify all functionality
  - Ensure all tests pass, ask the user if questions arise.
