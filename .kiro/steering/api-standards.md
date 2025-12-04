---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# REST API Standards

## HTTP Methods

- **GET**: Retrieve resources (no request body)
- **POST**: Create new resources (returns 201 Created)
- **PUT**: Update existing resources (returns 200 OK)
- **DELETE**: Remove resources (returns 200 OK or 204 No Content)
- **PATCH**: Partial updates (returns 200 OK)

## HTTP Status Codes

### Success Codes
- `200 OK`: Successful GET, PUT, PATCH, DELETE
- `201 Created`: Successful POST (resource created)
- `204 No Content`: Successful DELETE with no response body

### Client Error Codes
- `400 Bad Request`: Invalid request syntax or parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource does not exist
- `422 Unprocessable Entity`: Validation errors

### Server Error Codes
- `500 Internal Server Error`: Unexpected server error

## JSON Response Format

### Success Response
```json
{
  "data": { ... },
  "message": "Optional success message"
}
```

### List Response
```json
{
  "items": [ ... ],
  "count": 10,
  "total": 100
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400,
  "errors": [
    {
      "field": "field_name",
      "message": "Validation error message"
    }
  ]
}
```

## API Design Conventions

1. Use plural nouns for resource endpoints: `/events`, `/users`
2. Use path parameters for resource IDs: `/events/{event_id}`
3. Use query parameters for filtering: `/events?status=active`
4. Include proper CORS headers for web access
5. Validate all input data with appropriate error messages
6. Use consistent naming (snake_case for JSON keys)
7. Include timestamps (createdAt, updatedAt) on resources
8. Return the created/updated resource in response body

## FastAPI Specific

- Use Pydantic models for request/response validation
- Use `status_code` parameter in route decorators
- Use `HTTPException` for error responses
- Include proper type hints for all functions
- Add docstrings for API documentation
