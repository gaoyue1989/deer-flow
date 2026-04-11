# DeerFlow Testing Guidelines

## Best Practices

### Unit Test Organization

1. **Test file naming**: `test_*.py` in `backend/tests/` directory
2. **Test class naming**: `Test*` for test classes, `test_*` for test methods
3. **Fixtures**: Use `@pytest.fixture` for reusable test data
4. **Markers**: Use `@pytest.mark.*` for test categorization

### Test Categories

- **Unit tests**: Fast, isolated, no external dependencies
- **Integration tests**: Test component interactions
- **Live tests**: Require real API keys and config (skipped in CI)
- **E2E tests**: Full system testing

### Writing Effective Tests

1. **Arrange-Act-Assert** pattern
2. **One assertion per concept** (not necessarily one per test)
3. **Descriptive test names** that explain the scenario
4. **Clean teardown** - use fixtures with `yield` for cleanup

### Running Tests

```bash
# All tests
cd backend && uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_auth_jwt.py -v

# Specific test class
uv run pytest tests/test_auth_jwt.py::TestCreateAccessToken -v

# Specific test
uv run pytest tests/test_auth_jwt.py::TestCreateAccessToken::test_create_token_with_user_id -v

# Tests matching pattern
uv run pytest -k "auth" -v

# Rerun failed tests
uv run pytest --lf

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Test Dependencies

- **pytest**: Test runner
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **httpx**: Async HTTP client for testing
- **fastapi.testclient**: TestClient for FastAPI apps

### Common Patterns

#### Testing FastAPI Endpoints

```python
from fastapi.testclient import TestClient

def test_endpoint(client: TestClient):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

#### Testing with Fixtures

```python
@pytest.fixture
def mock_store(tmp_path):
    store = UserStore(base_dir=tmp_path)
    return store

def test_create_user(mock_store):
    user = mock_store.create(uuid4(), "test@example.com", "hash")
    assert user["email"] == "test@example.com"
```

#### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Live Tests

Live tests require valid API credentials and are skipped in CI:

```python
# Skip if no config.yaml
if not Path("config.yaml").exists():
    pytest.skip("No config.yaml found", allow_module_level=True)
```

Run live tests explicitly:
```bash
uv run pytest tests/test_client_live.py -v -s
```
