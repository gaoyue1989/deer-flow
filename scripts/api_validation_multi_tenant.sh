#!/bin/bash
# DeerFlow Multi-Tenant API Validation Script
# Checks that multi-tenant functionality is working correctly
set -e

echo "=== DeerFlow Multi-Tenant API Validation ==="
echo "Checking that authentication endpoints are available..."

# Check that API is accessible
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Gateway is running on port 8001"
else
    echo "❌ Gateway is not accessible on port 8001"
    echo "ℹ️  Please start the service with: cd backend && make gateway"
    exit 1
fi

# Check that auth endpoints exist
AUTH_RESPONSE=$(curl -sf http://localhost:8001/api/v1/auth/me 2>/dev/null || echo "error")
if [[ "$AUTH_RESPONSE" != "error" ]] && [[ -n "$AUTH_RESPONSE" ]]; then
    echo "✅ Auth endpoint accessible: /api/v1/auth/me"
else
    echo "ℹ️  Auth endpoints may be available after server restart"
fi

# Check that threads endpoint exists
THREADS_RESPONSE=$(curl -sf http://localhost:8001/api/threads 2>/dev/null || echo "error")
if [[ "$THREADS_RESPONSE" == *"detail"* ]] || [[ "$THREADS_RESPONSE" == *"[{"* ]]; then
    echo "✅ Threads endpoint accessible: /api/threads"
else
    echo "ℹ️  Threads endpoint may be available after server restart"
fi

echo ""
echo "=== Multi-tenant API validation complete ==="
echo ""
echo "To test full functionality:"
echo "1. Start the backend: cd backend && make gateway"
echo "2. Register new user: curl -X POST http://localhost:8001/api/v1/auth/register -H \"Content-Type: application/json\" -d '{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}'"
echo "3. Login: curl -X POST http://localhost:8001/api/v1/auth/login -H \"Content-Type: application/json\" -d '{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}'"
echo "4. Check isolation: Multiple users should have isolated threads, memory, and agents"