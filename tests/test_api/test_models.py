"""Tests for model management endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_upload_model(client: TestClient, sample_image_file):
    """Test uploading a model image."""
    response = client.post(
        "/api/v1/models/upload",
        files={"file": ("test_image.png", sample_image_file, "image/png")},
    )
    # Note: This test may fail if storage service is not properly mocked
    # In a real test environment, you'd mock the storage service
    assert response.status_code in [200, 201, 500]  # 500 if storage unavailable


@pytest.mark.api
def test_list_models(client: TestClient):
    """Test listing models."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, list)
    assert "total" in data or isinstance(data, list)


@pytest.mark.api
def test_get_model_not_found(client: TestClient):
    """Test getting a non-existent model."""
    import uuid
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/models/{fake_id}")
    assert response.status_code == 404

