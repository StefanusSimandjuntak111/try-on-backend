"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_models_health(client: TestClient):
    """Test ML models health check endpoint."""
    response = client.get("/api/v1/health/models")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "models" in data
    assert isinstance(data["models"], dict)


def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

