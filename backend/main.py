from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Event Management API",
    description="REST API for managing events with DynamoDB",
    version="1.0.0"
)

allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=3600,
)

dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'events-table')
table = dynamodb.Table(table_name)
users_table_name = os.getenv('USERS_TABLE', 'users-table')
users_table = dynamodb.Table(users_table_name)
registrations_table_name = os.getenv('REGISTRATIONS_TABLE', 'registrations-table')
registrations_table = dynamodb.Table(registrations_table_name)

VALID_STATUSES = ["active", "cancelled", "completed", "postponed"]


class UserCreate(BaseModel):
    userId: Optional[str] = Field(None, max_length=100, description="Optional custom user ID")
    name: str = Field(..., min_length=1, max_length=200, description="User's display name")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError("Name cannot be empty or whitespace only")
        return v


class User(BaseModel):
    userId: str = Field(..., max_length=100, description="Unique user identifier")
    name: str = Field(..., min_length=1, max_length=200, description="User's display name")
    createdAt: str = Field(..., description="ISO timestamp of creation")


class Registration(BaseModel):
    eventId: str = Field(..., max_length=100, description="Event identifier")
    userId: str = Field(..., max_length=100, description="User identifier")
    status: str = Field(..., description="Registration status: registered or waitlisted")
    waitlistPosition: Optional[int] = Field(None, description="Position in waitlist if waitlisted")
    registeredAt: str = Field(..., description="ISO timestamp of registration")


class UserRegistration(BaseModel):
    eventId: str = Field(..., description="Event identifier")
    eventTitle: str = Field(..., description="Event title")
    eventDate: str = Field(..., description="Event date")
    status: str = Field(..., description="Registration status: registered or waitlisted")
    waitlistPosition: Optional[int] = Field(None, description="Position in waitlist if waitlisted")
    registeredAt: str = Field(..., description="ISO timestamp of registration")


class RegistrationRequest(BaseModel):
    userId: str = Field(..., max_length=100, description="User ID to register")


class WaitlistConfig(BaseModel):
    waitlistEnabled: bool = Field(..., description="Enable or disable waitlist")


class Event(BaseModel):
    eventId: Optional[str] = Field(None, max_length=100, description="Optional custom event ID")
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: str = Field(..., min_length=1, max_length=2000, description="Event description")
    date: str = Field(..., description="Event date in ISO format or YYYY-MM-DD")
    location: str = Field(..., min_length=1, max_length=500, description="Event location")
    capacity: int = Field(..., gt=0, le=100000, description="Event capacity")
    organizer: str = Field(..., min_length=1, max_length=200, description="Event organizer")
    status: str = Field(default="active", description="Event status")
    waitlistEnabled: bool = Field(default=False, description="Whether waitlist is enabled")
    registeredCount: int = Field(default=0, ge=0, description="Current registration count")
    waitlistCount: int = Field(default=0, ge=0, description="Current waitlist count")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    capacity: Optional[int] = Field(None, gt=0, le=100000)
    organizer: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = None
    waitlistEnabled: Optional[bool] = None
    registeredCount: Optional[int] = Field(None, ge=0)
    waitlistCount: Optional[int] = Field(None, ge=0)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Date must be in ISO format (YYYY-MM-DDTHH:MM:SS)")
        return v


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )


@app.get("/")
def read_root():
    return {"message": "Event Management API", "version": "1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    user_id = user.userId if user.userId else str(uuid.uuid4())
    item = {
        'userId': user_id,
        'name': user.name,
        'createdAt': datetime.utcnow().isoformat()
    }
    
    try:
        users_table.put_item(Item=item)
        logger.info(f"Created user: {user_id}")
        return item
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user in database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/users/{user_id}")
def get_user(user_id: str):
    if not user_id or len(user_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    try:
        response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        logger.info(f"Retrieved user: {user_id}")
        return response['Item']
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/users/{user_id}/registrations")
def get_user_registrations(user_id: str):
    if not user_id or len(user_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    try:
        # Check if user exists
        user_response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in user_response:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Query registrations by userId using GSI
        response = registrations_table.query(
            IndexName='userId-index',
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        
        registrations = response.get('Items', [])
        
        # Enrich with event details
        user_registrations = []
        for reg in registrations:
            event_response = table.get_item(Key={'eventId': reg['eventId']})
            if 'Item' in event_response:
                event = event_response['Item']
                user_registrations.append({
                    'eventId': reg['eventId'],
                    'eventTitle': event.get('title', ''),
                    'eventDate': event.get('date', ''),
                    'status': reg['status'],
                    'waitlistPosition': reg.get('waitlistPosition'),
                    'registeredAt': reg['registeredAt']
                })
        
        logger.info(f"Retrieved {len(user_registrations)} registrations for user: {user_id}")
        return {"registrations": user_registrations, "count": len(user_registrations)}
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve registrations from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(event: Event):
    event_id = event.eventId if event.eventId else str(uuid.uuid4())
    item = {
        'eventId': event_id,
        'title': event.title,
        'description': event.description,
        'date': event.date,
        'location': event.location,
        'capacity': event.capacity,
        'organizer': event.organizer,
        'status': event.status,
        'waitlistEnabled': event.waitlistEnabled,
        'registeredCount': event.registeredCount,
        'waitlistCount': event.waitlistCount,
        'createdAt': datetime.utcnow().isoformat()
    }
    
    try:
        table.put_item(Item=item)
        logger.info(f"Created event: {event_id}")
        return item
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event in database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/events")
def list_events():
    try:
        response = table.scan()
        events = response.get('Items', [])
        logger.info(f"Retrieved {len(events)} events")
        return {"events": events, "count": len(events)}
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/events/{event_id}")
def get_event(event_id: str):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        logger.info(f"Retrieved event: {event_id}")
        return response['Item']
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.put("/events/{event_id}")
def update_event(event_id: str, event: EventUpdate):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            logger.warning(f"Event not found for update: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        updates = event.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_expr = "SET "
        expr_values = {}
        expr_names = {}
        
        for idx, (key, value) in enumerate(updates.items()):
            if idx > 0:
                update_expr += ", "
            expr_names[f"#{key}"] = key
            expr_values[f":{key}"] = value
            update_expr += f"#{key} = :{key}"
        
        update_expr += ", #updatedAt = :updatedAt"
        expr_names["#updatedAt"] = "updatedAt"
        expr_values[":updatedAt"] = datetime.utcnow().isoformat()
        
        response = table.update_item(
            Key={'eventId': event_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW"
        )
        
        logger.info(f"Updated event: {event_id}")
        return response['Attributes']
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event in database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.delete("/events/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(event_id: str):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            logger.warning(f"Event not found for deletion: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        table.delete_item(Key={'eventId': event_id})
        logger.info(f"Deleted event: {event_id}")
        return {"message": "Event deleted successfully", "eventId": event_id}
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post("/events/{event_id}/registrations", status_code=status.HTTP_201_CREATED)
def register_user_for_event(event_id: str, registration: RegistrationRequest):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    user_id = registration.userId
    
    try:
        # Check if event exists
        event_response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in event_response:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        event = event_response['Item']
        
        # Check if user exists
        user_response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in user_response:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already registered
        existing_reg = registrations_table.get_item(
            Key={'eventId': event_id, 'userId': user_id}
        )
        if 'Item' in existing_reg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already registered for this event"
            )
        
        # Get current counts
        registered_count = event.get('registeredCount', 0)
        waitlist_count = event.get('waitlistCount', 0)
        capacity = event.get('capacity', 0)
        waitlist_enabled = event.get('waitlistEnabled', False)
        
        # Determine registration status
        if registered_count < capacity:
            # Space available - register directly
            reg_status = "registered"
            waitlist_position = None
            new_registered_count = registered_count + 1
            new_waitlist_count = waitlist_count
        elif waitlist_enabled:
            # Event full but waitlist enabled
            reg_status = "waitlisted"
            waitlist_position = waitlist_count + 1
            new_registered_count = registered_count
            new_waitlist_count = waitlist_count + 1
        else:
            # Event full and no waitlist
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Event is full"
            )
        
        # Create registration
        registration_item = {
            'eventId': event_id,
            'userId': user_id,
            'status': reg_status,
            'registeredAt': datetime.utcnow().isoformat()
        }
        if waitlist_position is not None:
            registration_item['waitlistPosition'] = waitlist_position
        
        registrations_table.put_item(Item=registration_item)
        
        # Update event counts
        table.update_item(
            Key={'eventId': event_id},
            UpdateExpression='SET registeredCount = :rc, waitlistCount = :wc',
            ExpressionAttributeValues={
                ':rc': new_registered_count,
                ':wc': new_waitlist_count
            }
        )
        
        logger.info(f"Registered user {user_id} for event {event_id} with status {reg_status}")
        return registration_item
        
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user for event"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.delete("/events/{event_id}/registrations/{user_id}", status_code=status.HTTP_200_OK)
def unregister_user_from_event(event_id: str, user_id: str):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    if not user_id or len(user_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    try:
        # Check if registration exists
        reg_response = registrations_table.get_item(
            Key={'eventId': event_id, 'userId': user_id}
        )
        if 'Item' not in reg_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not registered for this event"
            )
        
        registration = reg_response['Item']
        reg_status = registration['status']
        
        # Get event
        event_response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in event_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        event = event_response['Item']
        
        # Delete the registration
        registrations_table.delete_item(Key={'eventId': event_id, 'userId': user_id})
        
        if reg_status == "registered":
            # User was registered - decrement count
            new_registered_count = max(0, event.get('registeredCount', 0) - 1)
            
            # Check if there's a waitlist to promote from
            waitlist_response = registrations_table.query(
                KeyConditionExpression='eventId = :eid',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':eid': event_id,
                    ':status': 'waitlisted'
                }
            )
            
            waitlisted_users = sorted(
                waitlist_response.get('Items', []),
                key=lambda x: x.get('waitlistPosition', 999999)
            )
            
            if waitlisted_users:
                # Promote first waitlisted user
                first_waitlisted = waitlisted_users[0]
                promoted_user_id = first_waitlisted['userId']
                
                # Update their registration to registered
                registrations_table.update_item(
                    Key={'eventId': event_id, 'userId': promoted_user_id},
                    UpdateExpression='SET #status = :status REMOVE waitlistPosition',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'registered'}
                )
                
                # Update waitlist positions for remaining users
                for i, waitlisted_user in enumerate(waitlisted_users[1:], start=1):
                    registrations_table.update_item(
                        Key={'eventId': event_id, 'userId': waitlisted_user['userId']},
                        UpdateExpression='SET waitlistPosition = :pos',
                        ExpressionAttributeValues={':pos': i}
                    )
                
                new_waitlist_count = max(0, event.get('waitlistCount', 0) - 1)
                # registered count stays the same (one out, one in)
            else:
                new_waitlist_count = event.get('waitlistCount', 0)
            
            # Update event counts
            table.update_item(
                Key={'eventId': event_id},
                UpdateExpression='SET registeredCount = :rc, waitlistCount = :wc',
                ExpressionAttributeValues={
                    ':rc': new_registered_count,
                    ':wc': new_waitlist_count
                }
            )
            
        elif reg_status == "waitlisted":
            # User was waitlisted - update positions
            waitlist_position = registration.get('waitlistPosition', 0)
            
            # Get all waitlisted users with higher positions
            waitlist_response = registrations_table.query(
                KeyConditionExpression='eventId = :eid',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':eid': event_id,
                    ':status': 'waitlisted'
                }
            )
            
            # Update positions for users after the removed one
            for waitlisted_user in waitlist_response.get('Items', []):
                if waitlisted_user['waitlistPosition'] > waitlist_position:
                    registrations_table.update_item(
                        Key={'eventId': event_id, 'userId': waitlisted_user['userId']},
                        UpdateExpression='SET waitlistPosition = :pos',
                        ExpressionAttributeValues={
                            ':pos': waitlisted_user['waitlistPosition'] - 1
                        }
                    )
            
            # Decrement waitlist count
            new_waitlist_count = max(0, event.get('waitlistCount', 0) - 1)
            table.update_item(
                Key={'eventId': event_id},
                UpdateExpression='SET waitlistCount = :wc',
                ExpressionAttributeValues={':wc': new_waitlist_count}
            )
        
        logger.info(f"Unregistered user {user_id} from event {event_id}")
        return {"message": "Successfully unregistered from event", "eventId": event_id, "userId": user_id}
        
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister user from event"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/events/{event_id}/registrations")
def get_event_registrations(event_id: str):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    try:
        # Check if event exists
        event_response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in event_response:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Query all registrations for this event
        response = registrations_table.query(
            KeyConditionExpression='eventId = :eid',
            ExpressionAttributeValues={':eid': event_id}
        )
        
        registrations = response.get('Items', [])
        
        # Separate registered and waitlisted
        registered = [r for r in registrations if r['status'] == 'registered']
        waitlisted = sorted(
            [r for r in registrations if r['status'] == 'waitlisted'],
            key=lambda x: x.get('waitlistPosition', 999999)
        )
        
        logger.info(f"Retrieved {len(registrations)} registrations for event: {event_id}")
        return {
            "eventId": event_id,
            "registered": registered,
            "waitlisted": waitlisted,
            "registeredCount": len(registered),
            "waitlistCount": len(waitlisted)
        }
        
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve registrations from database"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.put("/events/{event_id}/waitlist")
def configure_event_waitlist(event_id: str, config: WaitlistConfig):
    if not event_id or len(event_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID"
        )
    
    try:
        # Check if event exists
        event_response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in event_response:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Update waitlist configuration
        response = table.update_item(
            Key={'eventId': event_id},
            UpdateExpression='SET waitlistEnabled = :enabled',
            ExpressionAttributeValues={':enabled': config.waitlistEnabled},
            ReturnValues="ALL_NEW"
        )
        
        logger.info(f"Updated waitlist config for event {event_id}: {config.waitlistEnabled}")
        return response['Attributes']
        
    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update waitlist configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# Lambda handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
