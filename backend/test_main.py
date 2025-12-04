import pytest
from fastapi.testclient import TestClient
from moto import mock_dynamodb
import boto3
import os

os.environ['DYNAMODB_TABLE'] = 'events-table-test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope="function")
def dynamodb_table(aws_credentials):
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='events-table-test',
            KeySchema=[
                {'AttributeName': 'eventId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'eventId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table


@pytest.fixture
def client(dynamodb_table):
    from main import app
    import main
    main.table = dynamodb_table
    return TestClient(app)


def test_get_events_empty(client):
    """Test GET /events with empty database"""
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_get_events_with_status_filter(client):
    """Test GET /events?status=active"""
    response = client.get("/events?status=active")
    assert response.status_code == 200


def test_create_event(client):
    """Test POST /events"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "API Test Organizer",
        "description": "Testing API Gateway integration",
        "location": "API Test Location",
        "title": "API Gateway Test Event",
        "capacity": 200,
        "status": "active"
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "eventId" in data
    assert data["title"] == event_data["title"]
    assert data["capacity"] == event_data["capacity"]
    assert data["status"] == event_data["status"]


def test_create_and_get_event(client):
    """Test POST /events and then GET /events/{eventId}"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "API Test Organizer",
        "description": "Testing API Gateway integration",
        "location": "API Test Location",
        "title": "API Gateway Test Event",
        "capacity": 200,
        "status": "active"
    }
    
    create_response = client.post("/events", json=event_data)
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]
    
    get_response = client.get(f"/events/{event_id}")
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["eventId"] == event_id
    assert data["title"] == event_data["title"]


def test_update_event(client):
    """Test PUT /events/{eventId}"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "API Test Organizer",
        "description": "Testing API Gateway integration",
        "location": "API Test Location",
        "title": "API Gateway Test Event",
        "capacity": 200,
        "status": "active"
    }
    
    create_response = client.post("/events", json=event_data)
    event_id = create_response.json()["eventId"]
    
    update_data = {
        "title": "Updated API Gateway Test Event",
        "capacity": 250
    }
    
    update_response = client.put(f"/events/{event_id}", json=update_data)
    assert update_response.status_code == 200
    
    data = update_response.json()
    assert data["title"] == update_data["title"]
    assert data["capacity"] == update_data["capacity"]


def test_delete_event(client):
    """Test DELETE /events/{eventId}"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "API Test Organizer",
        "description": "Testing API Gateway integration",
        "location": "API Test Location",
        "title": "API Gateway Test Event",
        "capacity": 200,
        "status": "active"
    }
    
    create_response = client.post("/events", json=event_data)
    event_id = create_response.json()["eventId"]
    
    delete_response = client.delete(f"/events/{event_id}")
    assert delete_response.status_code in [200, 204]
    
    get_response = client.get(f"/events/{event_id}")
    assert get_response.status_code == 404


def test_full_crud_workflow(client):
    """Test complete CRUD workflow"""
    # Create
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "API Test Organizer",
        "description": "Testing API Gateway integration",
        "location": "API Test Location",
        "title": "API Gateway Test Event",
        "capacity": 200,
        "status": "active"
    }
    
    create_response = client.post("/events", json=event_data)
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]
    
    # Read
    get_response = client.get(f"/events/{event_id}")
    assert get_response.status_code == 200
    
    # Update
    update_data = {
        "title": "Updated API Gateway Test Event",
        "capacity": 250
    }
    update_response = client.put(f"/events/{event_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["title"] == update_data["title"]
    
    # Delete
    delete_response = client.delete(f"/events/{event_id}")
    assert delete_response.status_code in [200, 204]
    
    # Verify deletion
    get_after_delete = client.get(f"/events/{event_id}")
    assert get_after_delete.status_code == 404


def test_get_nonexistent_event(client):
    """Test GET /events/{eventId} with non-existent ID"""
    response = client.get("/events/nonexistent-id")
    assert response.status_code == 404


def test_update_nonexistent_event(client):
    """Test PUT /events/{eventId} with non-existent ID"""
    update_data = {"title": "Updated Title"}
    response = client.put("/events/nonexistent-id", json=update_data)
    assert response.status_code == 404


def test_delete_nonexistent_event(client):
    """Test DELETE /events/{eventId} with non-existent ID"""
    response = client.delete("/events/nonexistent-id")
    assert response.status_code == 404


def test_create_event_invalid_capacity(client):
    """Test POST /events with invalid capacity"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "Test Organizer",
        "description": "Test Description",
        "location": "Test Location",
        "title": "Test Event",
        "capacity": -10,
        "status": "active"
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 422


def test_create_event_invalid_status(client):
    """Test POST /events with invalid status"""
    event_data = {
        "date": "2024-12-15T00:00:00",
        "organizer": "Test Organizer",
        "description": "Test Description",
        "location": "Test Location",
        "title": "Test Event",
        "capacity": 100,
        "status": "invalid_status"
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 422


def test_health_check(client):
    """Test GET /health"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test GET /"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
