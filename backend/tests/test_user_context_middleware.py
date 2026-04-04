"""Tests for UserContextMiddleware."""

from fastapi import Request, Response

from app.gateway.auth.jwt import create_access_token
from app.gateway.middleware.user_context import UserContextMiddleware, get_user_id_from_request


def test_middleware_injects_user_id_from_bearer_token():
    """Test that middleware extracts user_id from Authorization header."""
    middleware = UserContextMiddleware(lambda app: None)

    token = create_access_token(data={"sub": "user-123", "role": "user"})

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "query_string": b"",
            "path": "/",
        },
    )

    async def call_next(req: Request) -> Response:
        return Response(content=b"OK")

    import asyncio

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
    assert getattr(request.state, "user_id", None) == "user-123"


def test_middleware_injects_user_id_from_cookie():
    """Test that middleware extracts user_id from HttpOnly cookie."""
    middleware = UserContextMiddleware(lambda app: None)

    token = create_access_token(data={"sub": "user-456", "role": "user"})

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"cookie", f"access_token={token}".encode())],
            "query_string": b"",
            "path": "/",
        },
    )

    async def call_next(req: Request) -> Response:
        return Response(content=b"OK")

    import asyncio

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
    assert getattr(request.state, "user_id", None) == "user-456"


def test_middleware_no_authentication():
    """Test that middleware handles requests without authentication."""
    middleware = UserContextMiddleware(lambda app: None)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "path": "/",
        },
    )

    async def call_next(req: Request) -> Response:
        return Response(content=b"OK")

    import asyncio

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
    assert getattr(request.state, "user_id", None) is None


def test_middleware_invalid_token():
    """Test that middleware handles invalid tokens gracefully."""
    middleware = UserContextMiddleware(lambda app: None)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"authorization", b"Bearer invalid-token")],
            "query_string": b"",
            "path": "/",
        },
    )

    async def call_next(req: Request) -> Response:
        return Response(content=b"OK")

    import asyncio

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
    assert getattr(request.state, "user_id", None) is None


def test_get_user_id_from_request():
    """Test get_user_id_from_request helper function."""
    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "path": "/",
        },
    )
    request.state.user_id = "user-789"

    user_id = get_user_id_from_request(request)
    assert user_id == "user-789"


def test_get_user_id_from_request_none():
    """Test get_user_id_from_request when no user_id is set."""
    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "path": "/",
        },
    )

    user_id = get_user_id_from_request(request)
    assert user_id is None
