# Testing

## Stack

- **pytest** — test runner
- **pytest-asyncio** — async tests
- **pytest-cov** — coverage
- **httpx** — async test client для FastAPI
- **factory_boy** — test data factories
- **testcontainers** — PostgreSQL, Redis, Kafka в Docker

## Структура

```
tests/
├── conftest.py           # Fixtures
├── factories/            # Factory Boy factories
│   ├── user.py
│   ├── order.py
│   └── cafe.py
├── unit/                 # Unit tests
│   ├── services/
│   └── utils/
├── integration/          # Integration tests
│   ├── api/
│   └── workers/
└── e2e/                  # End-to-end (опционально)
```

## Naming

```python
# Файлы
test_order_service.py
test_users_api.py

# Функции
def test_create_order_success():
def test_create_order_fails_after_deadline():
def test_create_order_exceeds_balance():
```

Формат: `test_{action}_{expected_outcome}`

## Fixtures

### Database
```python
@pytest.fixture
async def db_session():
    """Fresh database session with rollback."""
    async with async_session() as session:
        yield session
        await session.rollback()
```

### Factories
```python
# tests/factories/user.py
class UserFactory(factory.Factory):
    class Meta:
        model = User

    tgid = factory.Sequence(lambda n: 100000 + n)
    name = factory.Faker('name')
    office = factory.Faker('city')
    role = 'user'
    is_active = True
```

### API Client
```python
@pytest.fixture
async def client(app):
    """Async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_client(client, user):
    """Client with auth token."""
    token = create_access_token(user.tgid)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

## Примеры тестов

### Unit test
```python
async def test_calculate_weekly_spent(db_session):
    user = await UserFactory.create(session=db_session)
    orders = [
        await OrderFactory.create(user_tgid=user.tgid, total_price=100),
        await OrderFactory.create(user_tgid=user.tgid, total_price=200),
    ]

    result = await calculate_weekly_spent(db_session, user.tgid)

    assert result == Decimal("300.00")
```

### API test
```python
async def test_create_order_success(auth_client, cafe, menu_items):
    payload = {
        "cafe_id": cafe.id,
        "order_date": "2025-12-08",
        "items": [
            {"menu_item_id": menu_items[0].id, "quantity": 1}
        ]
    }

    response = await auth_client.post("/api/v1/orders", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["cafe_id"] == cafe.id
    assert len(data["items"]) == 1
```

### Parametrized test
```python
@pytest.mark.parametrize("status,expected_code", [
    ("pending", 204),
    ("confirmed", 400),
    ("cancelled", 400),
])
async def test_cancel_order_by_status(auth_client, status, expected_code):
    order = await OrderFactory.create(status=status)

    response = await auth_client.delete(f"/api/v1/orders/{order.id}")

    assert response.status_code == expected_code
```

## Coverage

- Минимум: 80% для `src/`
- Запуск: `pytest --cov=src --cov-report=html`
- CI блокирует PR при падении coverage

## Запуск

```bash
# Все тесты
pytest

# Конкретный файл
pytest tests/unit/services/test_order_service.py

# С coverage
pytest --cov=src --cov-report=term-missing

# Только unit
pytest tests/unit/

# Verbose
pytest -v
```
