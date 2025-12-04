# Event Management API - Deployment Summary

## API Endpoint
**Base URL:** https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/

## Available Endpoints

### Health Check
- **GET** `/health` - Check API health status

### Events CRUD Operations
- **GET** `/events` - List all events
- **POST** `/events` - Create a new event
- **GET** `/events/{event_id}` - Get a specific event
- **PUT** `/events/{event_id}` - Update an event
- **DELETE** `/events/{event_id}` - Delete an event

## Event Schema
```json
{
  "eventId": "string (auto-generated UUID)",
  "title": "string (1-200 chars)",
  "description": "string (1-2000 chars)",
  "date": "string (ISO format: YYYY-MM-DDTHH:MM:SS)",
  "location": "string (1-500 chars)",
  "capacity": "integer (1-100000)",
  "organizer": "string (1-200 chars)",
  "status": "string (active|cancelled|completed|postponed)",
  "createdAt": "string (ISO timestamp)",
  "updatedAt": "string (ISO timestamp, on updates)"
}
```

## Example Usage

### Create Event
```bash
curl -X POST https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tech Conference 2024",
    "description": "Annual technology conference",
    "date": "2024-12-15T09:00:00",
    "location": "San Francisco, CA",
    "capacity": 500,
    "organizer": "Tech Events Inc",
    "status": "active"
  }'
```

### List Events
```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events
```

### Get Specific Event
```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/{event_id}
```

### Update Event
```bash
curl -X PUT https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/{event_id} \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Event Title",
    "capacity": 600
  }'
```

### Delete Event
```bash
curl -X DELETE https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/{event_id}
```

## Infrastructure

### AWS Resources
- **API Gateway**: REST API with CORS enabled
- **Lambda Function**: Python 3.9 runtime with FastAPI + Mangum
- **DynamoDB Table**: `EventsApiStack-EventsTableD24865E5-K2DH1XAAUM9X`
- **Region**: us-west-2

### Features
- ✅ Full CRUD operations
- ✅ Input validation (field lengths, capacity range, date format, status values)
- ✅ Proper error handling with detailed messages
- ✅ CORS enabled for web access
- ✅ Structured logging
- ✅ Serverless architecture (pay-per-use)
- ✅ Auto-scaling with Lambda and DynamoDB
- ✅ Unit tests with 100% pass rate (14/14 tests)

## Testing
All unit tests pass successfully:
```bash
cd backend
python3 -m pytest test_main.py -v
# 14 passed in 1.22s
```

## Deployment
The API is deployed using AWS CDK:
```bash
cd infrastructure
cdk deploy
```

## Cost Optimization
- DynamoDB: Pay-per-request billing mode
- Lambda: Pay only for execution time
- API Gateway: Pay per API call
- No idle costs when not in use
