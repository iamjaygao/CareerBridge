#!/bin/bash
# Quick verification script for USERS module critical path

echo "=========================================="
echo "USERS MODULE CRITICAL PATH VERIFICATION"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "1. Running Python verification script..."
python3 scripts/verify_users_critical_path.py

echo ""
echo "2. Testing login endpoint..."
echo ""
echo "   Running: curl -X POST http://localhost:8000/api/v1/users/login/"
echo "   (This will fail if no user exists, but should return 400, not 404)"
echo ""

curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s -o /dev/null

echo ""
echo "Expected status codes:"
echo "   - 200 OK: Login successful"
echo "   - 400 Bad Request: Invalid credentials (but endpoint works)"
echo "   - 404 Not Found: PROBLEM - governance is blocking!"
echo ""
echo "=========================================="
echo "Verification complete!"
echo "=========================================="
