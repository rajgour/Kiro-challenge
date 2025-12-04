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

VALID_STATUSES = ["active", "cancelled", "completed", "postponed"]


class Event(BaseModel):
    eventId: Optional[str] = Field(None, max_length=100, description="Optional custom event ID")
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: str = Field(..., min_length=1, max_length=2000, description="Event description")
    date: str = Field(..., description="Event date in ISO format or YYYY-MM-DD")
    location: str = Field(..., min_length=1, max_length=500, description="Event location")
    capacity: int = Field(..., gt=0, le=100000, description="Event capacity")
    organizer: str = Field(..., min_length=1, max_length=200, description="Event organizer")
    status: str = Field(default="active", description="Event status")

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

# Lambda handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
