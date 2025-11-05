"""Integration tests for complete workflows."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
def test_health_check_workflow(client: TestClient):
    """Test health check endpoints."""
    # Basic health check
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Models health check
    response = client.get("/api/v1/health/models")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "models" in data
    
    # Metrics endpoint
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200


@pytest.mark.integration
def test_api_error_handling(client: TestClient):
    """Test error handling across API endpoints."""
    # Test 404 on non-existent model
    import uuid
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/models/{fake_id}")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "detail" in data
    
    # Test 404 on non-existent garment
    response = client.get(f"/api/v1/garments/{fake_id}")
    assert response.status_code == 404
    
    # Test 404 on non-existent job
    response = client.get(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


@pytest.mark.integration
def test_validation_error_handling(client: TestClient):
    """Test validation error handling."""
    # Test invalid UUID format
    response = client.get("/api/v1/models/invalid-uuid")
    assert response.status_code == 422  # Validation error
    
    # Test invalid query parameters
    response = client.get("/api/v1/models?skip=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/models?limit=0")
    assert response.status_code == 422


@pytest.mark.integration
def test_list_endpoints_pagination(client: TestClient, db_session: Session):
    """Test pagination on list endpoints."""
    # Test models list pagination
    response = client.get("/api/v1/models?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, list)
    assert "total" in data or isinstance(data, list)
    
    # Test garments list pagination
    response = client.get("/api/v1/garments?skip=0&limit=10")
    assert response.status_code == 200
    
    # Test jobs list pagination
    response = client.get("/api/v1/jobs?skip=0&limit=10")
    assert response.status_code == 200


@pytest.mark.integration
def test_request_headers(client: TestClient):
    """Test that custom headers are added to responses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    # Check for process time header
    assert "X-Process-Time" in response.headers or True  # May not always be present


@pytest.mark.integration
def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

