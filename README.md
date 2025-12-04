# Event Management API

A serverless REST API for managing events, built with FastAPI and deployed on AWS using Lambda, API Gateway, and DynamoDB.

## Project Structure

```
.
├── backend/                 # FastAPI application
│   ├── main.py             # Main API application
│   ├── test_main.py        # Unit tests
│   ├── requirements.txt    # Python dependencies
│   └── docs/               # Generated API documentation
├── infrastructure/          # AWS CDK infrastructure
│   ├── app.py              # CDK app entry point
│   ├── stacks/             # CDK stack definitions
│   └── requirements.txt    # CDK dependencies
└── .kiro/                  # Kiro IDE configuration
```

## Live API Endpoint

**Base URL:** `https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/`

## Quick Start

### Prerequisites

- Python 3.9+
- AWS CLI configured with credentials
- Node.js (for AWS CDK)

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Locally

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Run Tests

```bash
cd backend
python3 -m pytest test_main.py -v
```

## API Endpoints

### General
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |

### Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events` | List all events |
| GET | `/events?status=active` | Filter events by status |
| POST | `/events` | Create a new event |
| GET | `/events/{event_id}` | Get event by ID |
| PUT | `/events/{event_id}` | Update an event |
| DELETE | `/events/{event_id}` | Delete an event |
| PUT | `/events/{event_id}/waitlist` | Configure event waitlist |
| GET | `/events/{event_id}/registrations` | List event registrations |
| POST | `/events/{event_id}/registrations` | Register user for event |
| DELETE | `/events/{event_id}/registrations/{user_id}` | Unregister user from event |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a new user |
| GET | `/users/{user_id}` | Get user by ID |
| GET | `/users/{user_id}/registrations` | List user's registered events |

## Data Schemas

### Event Schema

```json
{
  "eventId": "string (optional, auto-generated if not provided)",
  "title": "string (required, 1-200 chars)",
  "description": "string (required, 1-2000 chars)",
  "date": "string (required, YYYY-MM-DD or ISO format)",
  "location": "string (required, 1-500 chars)",
  "capacity": "integer (required, 1-100000)",
  "organizer": "string (required, 1-200 chars)",
  "status": "string (active|cancelled|completed|postponed)",
  "waitlistEnabled": "boolean (default: false)",
  "registeredCount": "integer (default: 0)",
  "waitlistCount": "integer (default: 0)"
}
```

### User Schema

```json
{
  "userId": "string (optional, auto-generated if not provided)",
  "name": "string (required, 1-200 chars, non-whitespace)",
  "createdAt": "string (ISO timestamp, auto-generated)"
}
```

### Registration Schema

```json
{
  "eventId": "string (required)",
  "userId": "string (required)",
  "status": "string (registered|waitlisted)",
  "waitlistPosition": "integer (optional, only for waitlisted)",
  "registeredAt": "string (ISO timestamp)"
}
```

## Usage Examples

### Event Management

#### Create an Event with Waitlist

```bash
curl -X POST https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "my-event-123",
    "title": "Tech Conference 2024",
    "description": "Annual technology conference",
    "date": "2024-12-15",
    "location": "San Francisco, CA",
    "capacity": 500,
    "organizer": "Tech Events Inc",
    "status": "active",
    "waitlistEnabled": true
  }'
```

#### List All Events

```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events
```

#### Get Event by ID

```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123
```

#### Update an Event

```bash
curl -X PUT https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Conference Title",
    "capacity": 600
  }'
```

#### Delete an Event

```bash
curl -X DELETE https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123
```

### User Management

#### Create a User

```bash
curl -X POST https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson"
  }'
```

#### Get User by ID

```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/users/user-123
```

#### List User's Registrations

```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/users/user-123/registrations
```

### Registration Management

#### Register User for Event

```bash
curl -X POST https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123/registrations \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-123"
  }'
```

#### Unregister User from Event

```bash
curl -X DELETE https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123/registrations/user-123
```

#### List Event Registrations

```bash
curl https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123/registrations
```

#### Configure Event Waitlist

```bash
curl -X PUT https://yow9r9vsh6.execute-api.us-west-2.amazonaws.com/prod/events/my-event-123/waitlist \
  -H "Content-Type: application/json" \
  -d '{
    "waitlistEnabled": true
  }'
```

## Infrastructure Deployment

### Setup CDK

```bash
cd infrastructure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk
```

### Deploy

```bash
cd infrastructure
cdk bootstrap  # First time only
cdk deploy
```

### Destroy

```bash
cd infrastructure
cdk destroy
```

## Features

- **Event Management**: Create, read, update, and delete events
- **User Management**: Create users and track their registrations
- **Registration System**: Register users for events with capacity constraints
- **Waitlist Support**: Automatic waitlist management when events reach capacity
- **Automatic Promotion**: Waitlisted users are automatically promoted when spots open
- **Duplicate Prevention**: Prevents users from registering multiple times for the same event

## AWS Resources

- **API Gateway**: REST API with CORS enabled
- **Lambda**: Python 3.9 runtime with FastAPI + Mangum
- **DynamoDB Tables**:
  - Events table (partition key: eventId)
  - Users table (partition key: userId)
  - Registrations table (partition key: eventId, sort key: userId, GSI: userId-index)
- **Region**: us-west-2

## Documentation

API documentation is available in `backend/docs/` folder, generated using pdoc.

## License

MIT
