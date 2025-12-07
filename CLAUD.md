# FastAPI Clean Architecture Guidelines

## Architecture Overview

This codebase follows a clean architecture pattern with FastAPI, emphasizing separation of concerns, maintainability, and scalability. The architecture is organized into distinct layers with clear dependencies and responsibilities.

## Core Principles

### 1. Layered Architecture
- **API Layer**: Handle HTTP requests and responses
- **Service Layer**: Implement business logic
- **Repository Layer**: Manage data access
- **Model Layer**: Define data structures

### 2. Dependency Direction
```
API → Services → Repositories → Models
```
Dependencies always point inward, with outer layers depending on inner layers but not vice versa.

### 3. Separation of Concerns
Each layer has a single responsibility and clear boundaries.

## Project Structure

```
project/
├── app/                        # Main application package
│   ├── adapters/               # External service integrations
│   │   ├── db/                 # Database adapters
│   │   ├── email/              # Email service adapters
│   │   └── external_apis/      # Third-party API clients
│   ├── api/                    # FastAPI route handlers
│   │   ├── health.py           # Health check endpoints
│   │   └── v1/                 # API versioning
│   │       ├── users/          # User-related routes
│   │       ├── admin/          # Admin routes
│   │       └── websockets.py   # WebSocket endpoints
│   ├── handlers/               # Exception and error handlers
│   ├── middlewares/            # Custom middlewares
│   │   ├── cors_middleware.py  # CORS configuration
│   │   └── logging_middleware.py # Request logging
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic layer
│   ├── types/                  # Type definitions
│   │   ├── dtos/               # Pydantic models
│   │   └── exceptions/         # Custom exceptions
│   └── utils/                  # Shared utilities
├── models/                     # Database models (SQLAlchemy)
├── migrations/                 # Database migrations (Alembic)
├── tests/                      # Test suite
└── main.py                     # Application entry point
```

## Layer Responsibilities

### API Layer (`app/api/`)

**Purpose**: Handle HTTP protocol concerns

**Responsibilities**:
- Request validation and parsing
- Response formatting and serialization
- HTTP status code management
- Route parameter extraction
- Authentication/authorization middleware integration

**Best Practices**:
- Keep route handlers thin - delegate to services
- Use Pydantic models for request/response validation
- Implement consistent error handling
- Version your APIs from the start
- Group related routes in separate modules

**Example Pattern**:
```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await user_service.create_user(session, user_data, current_user)
```

### Service Layer (`app/services/`)

**Purpose**: Implement business logic and orchestrate operations

**Responsibilities**:
- Business rule enforcement
- Complex operation coordination
- Cross-cutting concerns (logging, caching)
- External service integration
- Data transformation between layers

**Best Practices**:
- Keep services focused on single business domains
- Make services stateless
- Handle business exceptions gracefully
- Use dependency injection for testability
- Implement transactional boundaries here

**Example Pattern**:
```python
async def create_user(session: AsyncSession, user_data: UserCreate) -> UserResponse:
    # Business logic validation
    if await user_repository.email_exists(session, user_data.email):
        raise BusinessRuleException("Email already exists")

    # Create user through repository
    user = await user_repository.create_user(session, user_data)

    # Additional business operations
    await notification_service.send_welcome_email(user.email)

    return UserResponse.from_orm(user)
```

### Repository Layer (`app/repositories/`)

**Purpose**: Abstract data access and provide clean data interface

**Responsibilities**:
- CRUD operations
- Query optimization
- Database transaction management
- Data mapping between ORM and business models
- Cache management

**Best Practices**:
- Create repository interfaces for testability
- Keep repositories focused on single entities
- Use async/await for all database operations
- Implement proper error handling for database constraints
- Abstract away ORM-specific details

**Example Pattern**:
```python
class UserRepository:
    async def create_user(self, session: AsyncSession, user_data: UserCreate) -> User:
        db_user = User(**user_data.dict())
        session.add(db_user)
        await session.flush()
        await session.refresh(db_user)
        return db_user

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
```

### Model Layer (`models/`)

**Purpose**: Define data structures and relationships

**Responsibilities**:
- Database schema definition
- Relationship mapping
- Data validation at the model level
- Index and constraint definitions

**Best Practices**:
- Use SQLAlchemy declarative models
- Define proper relationships with cascade rules
- Add appropriate indexes for query performance
- Use meaningful constraint names
- Document complex relationships

## Authentication & Authorization

### JWT Token Strategy
- **Access Tokens**: Short-lived for API access
- **Refresh Tokens**: Longer-lived for token renewal
- **Token Revocation**: Maintain blacklist for security

### Implementation Pattern
```python
# Authentication middleware
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt_token(token)
    user = await user_repository.get_by_id(session, payload.user_id)
    if not user:
        raise AuthenticationException("Invalid token")
    return user

# Authorization decorator
def require_role(required_role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user.role != required_role:
                raise AuthorizationException("Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## Database Design Patterns

### Async SQLAlchemy Setup
```python
# Database configuration
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    async with async_session() as session:
        yield session
```

### Migration Strategy
- Use Alembic for schema versioning
- Generate migrations automatically when possible
- Review all generated migrations before applying
- Use descriptive migration messages
- Test migrations in development before production

## Error Handling

### Exception Hierarchy
```python
class BaseApplicationException(Exception):
    """Base exception for all application errors"""
    pass

class ValidationException(BaseApplicationException):
    """Raised when input validation fails"""
    pass

class BusinessRuleException(BaseApplicationException):
    """Raised when business rules are violated"""
    pass

class AuthenticationException(BaseApplicationException):
    """Raised when authentication fails"""
    pass
```

### Global Exception Handler
```python
@app.exception_handler(BaseApplicationException)
async def application_exception_handler(request: Request, exc: BaseApplicationException):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "type": exc.__class__.__name__}
    )
```

## Configuration Management

### Environment-Based Configuration
```python
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### Configuration Categories
- **Database**: Connection strings, pool settings
- **Security**: JWT secrets, password policies
- **External APIs**: Third-party service credentials
- **Application**: Feature flags, business constants

## Development Best Practices

### Code Organization
- Group related functionality in modules
- Use consistent naming conventions
- Implement proper dependency injection
- Write comprehensive tests for each layer
- Document complex business logic

### Testing Strategy
```python
# Test structure mirrors source structure
tests/
├── unit/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── integration/
│   └── api/
└── conftest.py
```

### Type Safety
- Use type hints throughout the codebase
- Leverage Pydantic for runtime validation
- Implement strict MyPy configuration
- Use generics for reusable components

### Performance Considerations
- Implement async/await consistently
- Use database connection pooling
- Add caching at appropriate layers
- Monitor query performance
- Implement pagination for large datasets

## Deployment & Operations

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": app.version
    }
```

### Logging Strategy
- Use structured logging (JSON format)
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include correlation IDs for traceability
- Avoid logging sensitive information

### Security Considerations
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Set up proper CORS policies
- Regular dependency updates

This architecture provides a scalable, maintainable foundation that can be adapted to various FastAPI projects while maintaining clean code principles and separation of concerns.