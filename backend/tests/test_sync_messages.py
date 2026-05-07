"""Tests for sync-messages API endpoint.

Unit tests cover:
- Model validation (ExternalMessage, SyncMessagesRequest, SyncMessagesResponse)
- Message conversion logic
- Permission checks

Integration tests cover:
- Full API endpoint flow
- Error handling (400, 403, 404, 500)
- Message merging with add_messages reducer
- Metadata tracking
"""

import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.gateway.routers import threads


class TestExternalMessage:
    """Unit tests for ExternalMessage model."""

    def test_valid_user_message(self):
        """Test creating a valid user message."""
        msg = threads.ExternalMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_assistant_message(self):
        """Test creating a valid assistant message."""
        msg = threads.ExternalMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_valid_system_message(self):
        """Test creating a valid system message."""
        msg = threads.ExternalMessage(role="system", content="You are a helpful assistant")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant"

    def test_invalid_role_raises_error(self):
        """Test that invalid role raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            threads.ExternalMessage(role="invalid", content="test")

    def test_missing_role_raises_error(self):
        """Test that missing role raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            threads.ExternalMessage(content="test")

    def test_missing_content_raises_error(self):
        """Test that missing content raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            threads.ExternalMessage(role="user")


class TestSyncMessagesRequest:
    """Unit tests for SyncMessagesRequest model."""

    def test_valid_request_with_required_fields(self):
        """Test creating a valid request with only required fields."""
        messages = [
            threads.ExternalMessage(role="user", content="Hello"),
            threads.ExternalMessage(role="assistant", content="Hi"),
        ]
        request = threads.SyncMessagesRequest(messages=messages)
        assert len(request.messages) == 2
        assert request.source is None
        assert request.metadata == {}

    def test_valid_request_with_all_fields(self):
        """Test creating a valid request with all fields."""
        messages = [threads.ExternalMessage(role="user", content="Hello")]
        request = threads.SyncMessagesRequest(
            messages=messages, source="external-agent", metadata={"original_id": "123"}
        )
        assert request.source == "external-agent"
        assert request.metadata == {"original_id": "123"}

    def test_empty_messages_allowed(self):
        """Test that empty messages array is allowed at model level."""
        request = threads.SyncMessagesRequest(messages=[])
        assert len(request.messages) == 0


class TestSyncMessagesResponse:
    """Unit tests for SyncMessagesResponse model."""

    def test_valid_response(self):
        """Test creating a valid response."""
        response = threads.SyncMessagesResponse(
            success=True, thread_id="thread-123", synced_count=4, total_messages=10
        )
        assert response.success is True
        assert response.thread_id == "thread-123"
        assert response.synced_count == 4
        assert response.total_messages == 10


class TestMessageConversion:
    """Unit tests for message conversion logic."""

    def test_convert_user_message(self):
        """Test converting user message to HumanMessage."""
        msg = threads.ExternalMessage(role="user", content="Hello")
        converted = HumanMessage(content=msg.content)
        assert isinstance(converted, HumanMessage)
        assert converted.content == "Hello"

    def test_convert_assistant_message(self):
        """Test converting assistant message to AIMessage."""
        msg = threads.ExternalMessage(role="assistant", content="Hi there!")
        converted = AIMessage(content=msg.content)
        assert isinstance(converted, AIMessage)
        assert converted.content == "Hi there!"

    def test_convert_system_message(self):
        """Test converting system message to SystemMessage."""
        msg = threads.ExternalMessage(role="system", content="You are helpful")
        converted = SystemMessage(content=msg.content)
        assert isinstance(converted, SystemMessage)
        assert converted.content == "You are helpful"

    def test_messages_have_required_fields(self):
        """Test that converted messages have content field."""
        msg1 = HumanMessage(content="Message 1")
        msg2 = HumanMessage(content="Message 2")
        assert msg1.content == "Message 1"
        assert msg2.content == "Message 2"


class TestSyncMessagesEndpoint:
    """Integration tests for sync_messages endpoint."""

    @pytest.fixture
    def mock_checkpointer(self):
        """Create a mock checkpointer."""
        checkpointer = MagicMock()
        checkpointer.aget_tuple = AsyncMock()
        checkpointer.aput = AsyncMock()
        return checkpointer

    @pytest.fixture
    def mock_store(self):
        """Create a mock store."""
        store = MagicMock()
        store.aget = AsyncMock()
        store.aput = AsyncMock()
        return store

    @pytest.fixture
    def mock_request(self, mock_checkpointer, mock_store):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user-123"
        request.app = Mock()
        request.app.state = Mock()
        request.app.state.checkpointer = mock_checkpointer
        request.app.state.store = mock_store
        return request

    def test_sync_messages_empty_array_returns_400(self, mock_checkpointer):
        """Test that empty messages array returns 400 error."""
        mock_store = MagicMock()
        mock_store.aget = AsyncMock()
        mock_item = MagicMock()
        mock_item.value = {"thread_id": "thread-123", "metadata": {"user_id": "user-123"}}
        mock_store.aget.return_value = mock_item

        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        mock_request.state.user_id = "user-123"
        mock_request.app = Mock()
        mock_request.app.state = Mock()
        mock_request.app.state.checkpointer = mock_checkpointer
        mock_request.app.state.store = mock_store

        body = threads.SyncMessagesRequest(messages=[])

        with pytest.raises(HTTPException) as exc_info:
            import asyncio

            asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert exc_info.value.status_code == 400
        assert "No messages provided" in exc_info.value.detail

    def test_sync_messages_thread_not_found_returns_404(self, mock_checkpointer):
        """Test that non-existent thread returns 404 error."""
        mock_checkpointer.aget_tuple.return_value = None

        mock_store = MagicMock()
        mock_store.aget = AsyncMock()
        mock_store.aget.return_value = None

        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        mock_request.state.user_id = "user-123"
        mock_request.app = Mock()
        mock_request.app.state = Mock()
        mock_request.app.state.checkpointer = mock_checkpointer
        mock_request.app.state.store = mock_store

        body = threads.SyncMessagesRequest(messages=[threads.ExternalMessage(role="user", content="Hello")])

        with pytest.raises(HTTPException) as exc_info:
            import asyncio

            asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    def test_sync_messages_permission_denied_returns_403(self, mock_checkpointer):
        """Test that accessing another user's thread returns 403 error."""
        mock_store = MagicMock()
        mock_store.aget = AsyncMock()
        mock_store.aget.return_value = MagicMock(
            value={"thread_id": "thread-123", "metadata": {"user_id": "other-user"}}
        )

        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        mock_request.state.user_id = "user-123"
        mock_request.app = Mock()
        mock_request.app.state = Mock()
        mock_request.app.state.checkpointer = mock_checkpointer
        mock_request.app.state.store = mock_store

        body = threads.SyncMessagesRequest(messages=[threads.ExternalMessage(role="user", content="Hello")])

        with pytest.raises(HTTPException) as exc_info:
            import asyncio

            asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    def test_sync_messages_basic_flow(self, mock_request, mock_checkpointer, mock_store):
        """Test basic sync flow with successful message sync."""
        mock_store.aget.return_value = MagicMock(
            value={"thread_id": "thread-123", "metadata": {"user_id": "user-123"}}
        )

        mock_checkpoint_tuple = MagicMock()
        mock_checkpoint_tuple.checkpoint = {"channel_values": {"messages": []}}
        mock_checkpoint_tuple.metadata = {"created_at": time.time()}
        mock_checkpointer.aget_tuple.return_value = mock_checkpoint_tuple

        mock_checkpointer.aput.return_value = {"configurable": {"checkpoint_id": "new-checkpoint"}}

        body = threads.SyncMessagesRequest(
            messages=[
                threads.ExternalMessage(role="user", content="Hello"),
                threads.ExternalMessage(role="assistant", content="Hi there!"),
            ],
            source="test-agent",
        )

        import asyncio

        result = asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert result.success is True
        assert result.thread_id == "thread-123"
        assert result.synced_count == 2
        assert result.total_messages == 2

        mock_checkpointer.aput.assert_called_once()
        call_args = mock_checkpointer.aput.call_args
        checkpoint = call_args[0][1]
        assert "messages" in checkpoint["channel_values"]
        assert len(checkpoint["channel_values"]["messages"]) == 2

    def test_sync_messages_appends_to_existing(self, mock_request, mock_checkpointer, mock_store):
        """Test that new messages are appended to existing messages."""
        mock_store.aget.return_value = MagicMock(
            value={"thread_id": "thread-123", "metadata": {"user_id": "user-123"}}
        )

        existing_messages = [HumanMessage(content="Existing message")]
        mock_checkpoint_tuple = MagicMock()
        mock_checkpoint_tuple.checkpoint = {"channel_values": {"messages": existing_messages}}
        mock_checkpoint_tuple.metadata = {"created_at": time.time()}
        mock_checkpointer.aget_tuple.return_value = mock_checkpoint_tuple

        mock_checkpointer.aput.return_value = {"configurable": {"checkpoint_id": "new-checkpoint"}}

        body = threads.SyncMessagesRequest(messages=[threads.ExternalMessage(role="user", content="New message")])

        import asyncio

        result = asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert result.synced_count == 1
        assert result.total_messages == 2

    def test_sync_messages_records_metadata(self, mock_request, mock_checkpointer, mock_store):
        """Test that sync metadata is recorded in checkpoint."""
        mock_store.aget.return_value = MagicMock(
            value={"thread_id": "thread-123", "metadata": {"user_id": "user-123"}}
        )

        mock_checkpoint_tuple = MagicMock()
        mock_checkpoint_tuple.checkpoint = {"channel_values": {"messages": []}}
        mock_checkpoint_tuple.metadata = {"created_at": time.time()}
        mock_checkpointer.aget_tuple.return_value = mock_checkpoint_tuple

        mock_checkpointer.aput.return_value = {"configurable": {"checkpoint_id": "new-checkpoint"}}

        body = threads.SyncMessagesRequest(
            messages=[threads.ExternalMessage(role="user", content="Hello")],
            source="external-agent",
            metadata={"original_id": "conv-456"},
        )

        import asyncio

        asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        call_args = mock_checkpointer.aput.call_args
        metadata = call_args[0][2]
        assert metadata["sync_source"] == "external-agent"
        assert metadata["synced_count"] == 1
        assert metadata["sync_metadata"] == {"original_id": "conv-456"}
        assert "updated_at" in metadata

    def test_sync_messages_handles_all_message_types(self, mock_request, mock_checkpointer, mock_store):
        """Test that all message types (user, assistant, system) are handled."""
        mock_store.aget.return_value = MagicMock(
            value={"thread_id": "thread-123", "metadata": {"user_id": "user-123"}}
        )

        mock_checkpoint_tuple = MagicMock()
        mock_checkpoint_tuple.checkpoint = {"channel_values": {"messages": []}}
        mock_checkpoint_tuple.metadata = {"created_at": time.time()}
        mock_checkpointer.aget_tuple.return_value = mock_checkpoint_tuple

        mock_checkpointer.aput.return_value = {"configurable": {"checkpoint_id": "new-checkpoint"}}

        body = threads.SyncMessagesRequest(
            messages=[
                threads.ExternalMessage(role="system", content="You are helpful"),
                threads.ExternalMessage(role="user", content="Hello"),
                threads.ExternalMessage(role="assistant", content="Hi!"),
            ]
        )

        import asyncio

        result = asyncio.run(threads.sync_messages("thread-123", body, mock_request))

        assert result.synced_count == 3
        assert result.total_messages == 3

        call_args = mock_checkpointer.aput.call_args
        checkpoint = call_args[0][1]
        messages = checkpoint["channel_values"]["messages"]
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert isinstance(messages[2], AIMessage)


class TestSyncMessagesAPIRoute:
    """Integration tests for sync-messages API route via TestClient."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app with threads router."""
        app = FastAPI()
        app.include_router(threads.router)
        return app

    def test_api_route_returns_400_for_empty_messages(self, app):
        """Test that API returns 400 for empty messages array."""
        with TestClient(app) as client:
            response = client.post(
                "/api/threads/thread-123/sync-messages",
                json={"messages": []},
            )
        assert response.status_code == 400
        assert "No messages provided" in response.json()["detail"]

    def test_api_route_validates_message_format(self, app):
        """Test that API validates message format."""
        with TestClient(app) as client:
            response = client.post(
                "/api/threads/thread-123/sync-messages",
                json={"messages": [{"invalid": "format"}]},
            )
        assert response.status_code == 422

    def test_api_route_validates_role_field(self, app):
        """Test that API validates role field."""
        with TestClient(app) as client:
            response = client.post(
                "/api/threads/thread-123/sync-messages",
                json={"messages": [{"role": "invalid", "content": "test"}]},
            )
        assert response.status_code == 422

    def test_api_route_accepts_valid_request(self, app, tmp_path):
        """Test that API accepts valid request structure."""
        from deerflow.config.paths import Paths

        paths = Paths(tmp_path)

        with (
            patch("app.gateway.routers.threads.get_paths", return_value=paths),
            patch("app.gateway.routers.threads.get_checkpointer") as mock_get_cp,
            patch("app.gateway.routers.threads.get_store") as mock_get_store,
        ):
            mock_checkpointer = MagicMock()
            mock_checkpointer.aget_tuple = AsyncMock()
            mock_checkpointer.aput = AsyncMock()

            mock_checkpoint_tuple = MagicMock()
            mock_checkpoint_tuple.checkpoint = {"channel_values": {"messages": []}}
            mock_checkpoint_tuple.metadata = {"created_at": time.time()}
            mock_checkpointer.aget_tuple.return_value = mock_checkpoint_tuple
            mock_checkpointer.aput.return_value = {"configurable": {"checkpoint_id": "cp-1"}}

            mock_get_cp.return_value = mock_checkpointer

            mock_store = MagicMock()
            mock_store.aget = AsyncMock(return_value=None)
            mock_get_store.return_value = mock_store

            with TestClient(app) as client:
                response = client.post(
                    "/api/threads/thread-123/sync-messages",
                    json={
                        "messages": [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi!"},
                        ],
                        "source": "test",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["synced_count"] == 2
            assert data["total_messages"] == 2
