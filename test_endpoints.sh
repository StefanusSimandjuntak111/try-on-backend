#!/bin/bash

echo "=== Testing Try-On Backend API on port 9000 ==="
echo ""

echo "1. Root endpoint:"
curl -s http://localhost:8500/ | jq .
echo ""

echo "2. Health check:"
curl -s http://localhost:8500/api/v1/health | jq .
echo ""

echo "3. Models health:"
curl -s http://localhost:8500/api/v1/health/models | jq .
echo ""

echo "4. List models:"
curl -s http://localhost:8500/api/v1/models | jq .
echo ""

echo "5. List garments:"
curl -s http://localhost:8500/api/v1/garments | jq .
echo ""

echo "6. List jobs:"
curl -s http://localhost:8500/api/v1/jobs | jq .
echo ""

echo "✅ All endpoints tested!"
echo ""
echo "📚 API Docs: http://localhost:8500/docs"

