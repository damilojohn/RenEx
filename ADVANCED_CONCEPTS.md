# Advanced Concepts & Architectural Patterns in RenEx Backend

This document explains the advanced software engineering patterns, architectural decisions, and best practices used in this FastAPI backend implementation, designed for intermediate engineers.

## 1. **Repository Pattern & Service Layer Abstraction**

### Current Implementation:
We use a **Service Layer** pattern rather than a strict Repository pattern. This is a pragmatic choice for FastAPI.

### Architecture Decision:
```python
# Service layer encapsulates business logic
async def create_listing(
    listing_data: ListingCreateRequest,
    user_id: UUID,
    session: AsyncSession
) -> ListingResponse:
    # Business rules
    if listing_data.start_time >= listing_data.end_time:
        raise HTTPException(...)
    
    # Data access
    new_listing = Listings(...)
    session.add(new_listing)
    
    # Return DTO
    return ListingResponse.model_validate(new_listing)
```

### Why This Approach?
- **FastAPI Context**: FastAPI's dependency injection handles session management
- **Simplicity**: Avoids over-engineering for MVP
- **Flexibility**: Easy to refactor to Repository pattern later if needed

### Alternative: Full Repository Pattern
```python
# More complex but better for large teams
class ListingRepository:
    async def create(self, listing: Listings) -> Listings: ...
    async def get_by_id(self, id: UUID) -> Listings: ...

class ListingService:
    def __init__(self, repo: ListingRepository):
        self.repo = repo
```

### Trade-offs:
- **Current**: Simpler, faster to develop, sufficient for MVP
- **Repository**: Better testability, clearer separation, more boilerplate

---

## 2. **Domain-Driven Design (DDD) Concepts**

### Bounded Contexts:
```
Auth Context    → User management, authentication
Listings Context → Energy listings, feeds
Swaps Context   → Swap transactions, negotiations
```

### Aggregate Roots:
- **RenExUser**: Root of user aggregate
- **Listings**: Root of listing aggregate (owns swaps)
- **Swap**: Child entity of listing aggregate

### Invariants & Business Rules:

#### Listing Invariants:
```python
# Invariant: Start time must be before end time
if listing_data.start_time >= listing_data.end_time:
    raise HTTPException(400, "Start time must be before end time")

# Invariant: Volume must be positive
volume: float = Field(..., gt=0)
```

#### Swap Invariants:
```python
# Invariant: Cannot swap with own listing
if listing.user_id == initiator_id:
    raise HTTPException(400, "Cannot create swap for your own listing")

# Invariant: Proposed volume cannot exceed available
if swap_data.proposed_volume > listing.volume:
    raise HTTPException(400, "Volume exceeds available")
```

### Domain Events (Future Enhancement):
```python
# Could emit events for:
# - ListingCreated
# - SwapRequested
# - SwapAccepted
# - SwapCompleted
```

---

## 3. **Transaction Management & Consistency Patterns**

### Current Approach: Session-Level Transactions
```python
async def create_listing(...):
    try:
        new_listing = Listings(...)
        session.add(new_listing)
        await session.commit()  # Single transaction
    except Exception:
        await session.rollback()
```

### Distributed Transaction Considerations:

#### Problem: Cross-Aggregate Operations
```python
# What if we need to:
# 1. Create swap
# 2. Update listing volume
# 3. Send notification
# All must succeed or all fail
```

#### Solution: Saga Pattern (for future)
```python
# Compensating transactions
async def create_swap_saga(swap_data):
    try:
        swap = await create_swap(...)
        await update_listing_volume(...)
        await send_notification(...)
    except Exception:
        # Compensate: undo previous steps
        await cancel_swap(swap.id)
        await revert_listing_volume(...)
```

### Optimistic Locking (Not Implemented, But Consider):
```python
# Prevent concurrent updates
class Listings(RecordModel):
    version: Mapped[int] = mapped_column(Integer, default=0)

# In update:
if listing.version != expected_version:
    raise HTTPException(409, "Concurrent modification detected")
listing.version += 1
```

---

## 4. **Query Optimization & N+1 Problem**

### Current Implementation:
```python
# Potential N+1 problem in get_swap_by_id
listing = await session.get(Listings, swap.listing_id)
initiator = await session.get(RenExUser, swap.initiator_id)
recipient = await session.get(RenExUser, swap.recipient_id)
# 3 separate queries
```

### Solution: Eager Loading
```python
from sqlalchemy.orm import selectinload, joinedload

# Option 1: Joinedload (single query with JOIN)
result = await session.execute(
    select(Swap)
    .options(
        joinedload(Swap.listing),
        joinedload(Swap.initiator),
        joinedload(Swap.recipient)
    )
    .filter(Swap.id == swap_id)
)
swap = result.scalar_one()

# Option 2: Selectinload (separate optimized queries)
result = await session.execute(
    select(Swap)
    .options(
        selectinload(Swap.listing),
        selectinload(Swap.initiator),
        selectinload(Swap.recipient)
    )
    .filter(Swap.id == swap_id)
)
```

### Query Optimization Patterns:

#### Indexing Strategy:
```python
# Strategic indexes for common queries
class Listings(RecordModel):
    user_id: Mapped[UUID] = mapped_column(..., index=True)  # Filter by user
    status: Mapped[str] = mapped_column(..., index=True)    # Filter by status
    start_time: Mapped[datetime] = mapped_column(..., index=True)  # Time range queries
```

#### Composite Indexes (Future):
```python
# For queries like: WHERE status='active' AND energy_type='solar'
Index('idx_status_energy', 'status', 'energy_type')
```

---

## 5. **CQRS Pattern (Command Query Responsibility Segregation)**

### Current: Single Model
```python
# Same model for reads and writes
class Listings(RecordModel):
    # Used for both creating and querying
```

### CQRS Approach (Advanced):
```python
# Separate read/write models
class ListingWriteModel(RecordModel):
    # Normalized, optimized for writes
    pass

class ListingReadModel(Base):
    # Denormalized, optimized for reads
    # Could include computed fields, joins, etc.
    user_name: str  # Denormalized from users table
    match_count: int  # Computed field
```

### When to Use CQRS:
- **Current**: Not needed - read/write patterns are similar
- **Future**: If we add analytics, reporting, or complex read queries

---

## 6. **Event Sourcing Considerations**

### Current: State-Based Storage
```python
# We store current state
listing.status = "active"
listing.volume = 100.0
```

### Event Sourcing Alternative:
```python
# Store events instead
class ListingEvent(Base):
    event_type: str  # "ListingCreated", "VolumeUpdated", "StatusChanged"
    payload: JSON
    timestamp: datetime

# Reconstruct state from events
def get_listing_state(listing_id):
    events = get_events(listing_id)
    return apply_events(events)
```

### When Event Sourcing Makes Sense:
- Audit requirements
- Complex state transitions
- Need to replay events
- Temporal queries ("what was the state at time X?")

### Current: Not needed for MVP, but good to understand

---

## 7. **API Versioning Strategy**

### Current: No Versioning
```python
base_router = APIRouter(prefix="/renex/api")
```

### Versioning Approaches:

#### URL Versioning:
```python
base_router = APIRouter(prefix="/renex/api/v1")
```

#### Header Versioning:
```python
@router.get("/listings/")
async def get_listings(
    request: Request,
    api_version: str = Header(..., alias="API-Version")
):
    if api_version == "v2":
        return v2_response_format()
    return v1_response_format()
```

#### Content Negotiation:
```python
@router.get("/listings/", response_model=Union[ListingResponseV1, ListingResponseV2])
async def get_listings(accept: str = Header(...)):
    if "application/vnd.renex.v2+json" in accept:
        return ListingResponseV2(...)
    return ListingResponseV1(...)
```

### Recommendation: Add versioning before public release

---

## 8. **Caching Strategy**

### Current: No Caching
All queries hit the database directly.

### Caching Layers:

#### Application-Level Caching:
```python
from functools import lru_cache
from cachetools import TTLCache

# Cache user lookups (TTL: 5 minutes)
user_cache = TTLCache(maxsize=1000, ttl=300)

async def get_user_cached(user_id: UUID):
    if user_id in user_cache:
        return user_cache[user_id]
    user = await get_user(user_id)
    user_cache[user_id] = user
    return user
```

#### Redis Caching:
```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost")

async def get_feed_cached(user_id, filters):
    cache_key = f"feed:{user_id}:{hash(filters)}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    feed = await get_feed_listings(...)
    await redis_client.setex(cache_key, 300, json.dumps(feed))
    return feed
```

#### Database Query Caching:
```python
# SQLAlchemy query caching (requires dogpile.cache)
from dogpile.cache import make_region

cache_region = make_region().configure(
    'dogpile.cache.redis',
    arguments={'url': 'redis://localhost'}
)

@cache_region.cache_on_arguments()
def get_listing(listing_id):
    return session.query(Listings).filter_by(id=listing_id).one()
```

### Cache Invalidation Strategy:
```python
# Invalidate on updates
async def update_listing(...):
    listing = await update_listing(...)
    await redis_client.delete(f"listing:{listing.id}")
    await redis_client.delete(f"feed:*")  # Invalidate all feeds
    return listing
```

---

## 9. **Security Patterns & Best Practices**

### Current Security Measures:

#### 1. Password Hashing:
```python
# Using Argon2 (memory-hard, resistant to GPU attacks)
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__time_cost=4,
    argon2__memory_cost=65536,
    argon2__parallelism=4
)
```

#### 2. JWT Token Security:
```python
# Separate secrets for access/refresh tokens
JWT_SECRET_KEY  # For access tokens (short-lived)
JWT_REFRESH_SECRET  # For refresh tokens (long-lived)

# Token expiration
access_token: 15 minutes (JWT_EXP)
refresh_token: 7 days (JWT_REFRESH_EXP)
```

#### 3. SQL Injection Prevention:
```python
# SQLAlchemy parameterized queries (automatic)
result = await session.execute(
    select(Listings).filter(Listings.user_id == user_id)
    # user_id is automatically parameterized
)
```

### Additional Security Considerations:

#### Rate Limiting (Not Implemented):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/listings/")
@limiter.limit("10/minute")
async def create_listing(...):
    ...
```

#### Input Sanitization:
```python
# Pydantic automatically validates, but consider:
from pydantic import validator

class ListingCreateRequest(BaseModel):
    description: Optional[str]
    
    @validator('description')
    def sanitize_html(cls, v):
        # Remove HTML tags, prevent XSS
        return bleach.clean(v) if v else v
```

#### CORS Configuration:
```python
# Current: Allows all origins (development only)
allow_origins=["*"]

# Production: Specific origins
allow_origins=[
    "https://ren-ex.vercel.app",
    "https://www.renex.com"
]
```

---

## 10. **Error Handling & Observability**

### Current Error Handling:
```python
try:
    # Operation
except Exception as e:
    await session.rollback()
    raise HTTPException(500, f"Error: {str(e)}")
```

### Advanced Error Handling:

#### Custom Exception Hierarchy:
```python
class RenExException(Exception):
    """Base exception"""
    pass

class ListingNotFoundError(RenExException):
    """Domain-specific exception"""
    pass

class InsufficientVolumeError(RenExException):
    """Business rule violation"""
    pass

# In service:
if not listing:
    raise ListingNotFoundError(f"Listing {id} not found")

# In views:
try:
    result = await create_listing(...)
except ListingNotFoundError as e:
    raise HTTPException(404, str(e))
except InsufficientVolumeError as e:
    raise HTTPException(400, str(e))
```

#### Structured Logging:
```python
import structlog

logger = structlog.get_logger()

async def create_listing(...):
    logger.info(
        "listing_created",
        user_id=str(user_id),
        listing_type=listing_data.listing_type,
        volume=listing_data.volume
    )
```

#### Error Tracking (Sentry):
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1
)

# Automatic error tracking
```

---

## 11. **Database Migration Strategy**

### Current: Auto-Migration
```python
# Creates tables on startup
await conn.run_sync(Base.metadata.create_all)
```

### Production Approach: Alembic Migrations
```python
# alembic.ini
[alembic]
script_location = alembic

# alembic/env.py
from src.database import Base
target_metadata = Base.metadata

# Generate migration
alembic revision --autogenerate -m "Add listings table"

# Apply migration
alembic upgrade head
```

### Migration Best Practices:
- Never auto-generate in production
- Review generated migrations
- Test migrations on staging
- Have rollback strategy
- Version control all migrations

---

## 12. **Testing Strategy**

### Current: No Tests (MVP)

### Testing Pyramid:

#### Unit Tests:
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_listing_validates_time_range():
    session = AsyncMock()
    listing_data = ListingCreateRequest(
        start_time=datetime(2024, 1, 15, 18),
        end_time=datetime(2024, 1, 15, 8)  # Invalid
    )
    
    with pytest.raises(HTTPException) as exc:
        await create_listing(listing_data, user_id, session)
    
    assert exc.value.status_code == 400
```

#### Integration Tests:
```python
@pytest.mark.asyncio
async def test_create_listing_integration():
    async with get_test_session() as session:
        user = await create_test_user(session)
        listing = await create_listing(
            test_listing_data,
            user.id,
            session
        )
        assert listing.id is not None
        assert listing.user_id == user.id
```

#### API Tests:
```python
from fastapi.testclient import TestClient

def test_create_listing_endpoint():
    client = TestClient(app)
    response = client.post(
        "/renex/api/listings/",
        json=listing_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
```

---

## 13. **Performance Optimization Patterns**

### Database Query Optimization:

#### Select Only Needed Fields:
```python
# Instead of:
listing = await session.get(Listings, id)

# Use:
result = await session.execute(
    select(Listings.id, Listings.volume, Listings.price)
    .filter(Listings.id == id)
)
```

#### Batch Operations:
```python
# Instead of N queries:
for listing_id in listing_ids:
    listing = await get_listing(listing_id)

# Use:
listings = await session.execute(
    select(Listings).filter(Listings.id.in_(listing_ids))
).scalars().all()
```

#### Connection Pooling:
```python
# Already configured:
create_async_engine(
    url=conn_string,
    pool_size=5,        # Base pool size
    max_overflow=10,    # Additional connections
    pool_recycle=1800   # Recycle connections after 30 min
)
```

### Async Optimization:
```python
# Parallel independent queries:
import asyncio

listing, user = await asyncio.gather(
    session.get(Listings, listing_id),
    session.get(RenExUser, user_id)
)
```

---

## 14. **API Design Patterns**

### HATEOAS (Hypermedia as the Engine of Application State):
```python
class ListingResponse(BaseModel):
    id: UUID
    volume: float
    links: Dict[str, str] = Field(default_factory=dict)
    
    def add_links(self, request: Request):
        self.links = {
            "self": str(request.url_for("get_listing", listing_id=self.id)),
            "swaps": str(request.url_for("get_listing_swaps", listing_id=self.id)),
            "update": str(request.url_for("update_listing", listing_id=self.id))
        }
```

### Pagination Patterns:
```python
# Current: Page-based
class ListingFeedResponse(BaseModel):
    listings: List[ListingResponse]
    page: int
    page_size: int
    total: int

# Alternative: Cursor-based (better for large datasets)
class CursorPaginatedResponse(BaseModel):
    items: List[ListingResponse]
    next_cursor: Optional[str]
    has_more: bool
```

### Filtering & Sorting:
```python
# Current: Basic filtering
query = query.filter(Listings.status == "active")

# Advanced: Dynamic filtering
class ListingFilters(BaseModel):
    status: Optional[str] = None
    energy_type: Optional[str] = None
    min_volume: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[str] = None

def apply_filters(query, filters: ListingFilters):
    if filters.status:
        query = query.filter(Listings.status == filters.status)
    if filters.min_volume:
        query = query.filter(Listings.volume >= filters.min_volume)
    # ... etc
    return query
```

---

## 15. **Microservices Considerations**

### Current: Monolithic Architecture
All modules in single FastAPI application.

### When to Split:

#### Service Boundaries:
```
Auth Service      → User management, authentication
Listings Service  → Listings, feeds, search
Swaps Service     → Swap transactions, negotiations
Notifications Service → Email, push notifications
```

#### Communication Patterns:
```python
# Synchronous: HTTP/REST
# Asynchronous: Message Queue (RabbitMQ, Kafka)

# Event-driven:
async def on_listing_created(listing: Listings):
    await message_queue.publish(
        "listing.created",
        {"listing_id": str(listing.id)}
    )
```

### Service Mesh (Advanced):
- Istio, Linkerd for service-to-service communication
- Circuit breakers, retries, timeouts
- Not needed for MVP, but understand for scale

---

## 16. **Data Consistency Patterns**

### Eventual Consistency:
```python
# Current: Strong consistency (ACID transactions)
# All operations in single transaction

# Eventual consistency example:
# 1. Create swap
# 2. Publish event
# 3. Async handlers update related data
# 4. Eventually all systems consistent
```

### Saga Pattern (for distributed transactions):
```python
class CreateSwapSaga:
    async def execute(self, swap_data):
        steps = [
            self.create_swap,
            self.update_listing,
            self.send_notification
        ]
        
        completed = []
        try:
            for step in steps:
                result = await step(swap_data)
                completed.append((step, result))
        except Exception as e:
            # Compensate in reverse order
            for step, result in reversed(completed):
                await step.compensate(result)
            raise
```

---

## 17. **Monitoring & Observability**

### Metrics:
```python
from prometheus_client import Counter, Histogram

listing_created = Counter('listings_created_total', 'Total listings created')
listing_creation_time = Histogram('listing_creation_seconds', 'Time to create listing')

@listing_creation_time.time()
async def create_listing(...):
    listing_created.inc()
    # ... create listing
```

### Distributed Tracing:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def create_listing(...):
    with tracer.start_as_current_span("create_listing") as span:
        span.set_attribute("user_id", str(user_id))
        span.set_attribute("listing_type", listing_data.listing_type)
        # ... create listing
```

---

## 18. **Design Patterns Used**

### Dependency Injection:
```python
# FastAPI's dependency injection system
async def create_listing(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    # Dependencies injected automatically
```

### Factory Pattern:
```python
# Session factory
async def create_async_session(engine: AsyncEngine):
    return async_sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine
    )
```

### Strategy Pattern (Implicit):
```python
# Different validation strategies
def validate_listing(listing_data):
    if listing_data.listing_type == ListingType.SUPPLY:
        return validate_supply_listing(listing_data)
    else:
        return validate_demand_listing(listing_data)
```

---

## 19. **Scalability Considerations**

### Horizontal Scaling:
- Stateless API (JWT tokens, no server-side sessions)
- Database connection pooling
- Read replicas for queries
- Write sharding by user_id or region

### Vertical Scaling:
- Current: Single server
- Future: Load balancer → Multiple app servers
- Database: Master-replica setup

### Caching Strategy:
- Application cache for frequently accessed data
- CDN for static assets (if any)
- Redis for session data and hot data

---

## 20. **Code Quality & Maintainability**

### Type Safety:
```python
# Comprehensive type hints
async def create_listing(
    listing_data: ListingCreateRequest,  # Input type
    user_id: UUID,                        # Parameter type
    session: AsyncSession                 # Dependency type
) -> ListingResponse:                     # Return type
    ...
```

### Documentation:
```python
"""Create a new energy listing

Args:
    listing_data: Validated listing creation data
    user_id: ID of the user creating the listing
    session: Database session

Returns:
    ListingResponse with created listing data

Raises:
    HTTPException: If validation fails or user not found
"""
```

### Code Organization:
- Modular structure (auth, listings, swaps)
- Clear separation of concerns
- Consistent naming conventions
- DRY principle (Don't Repeat Yourself)

---

## Summary: Key Architectural Decisions

1. **Service Layer over Repository**: Simpler for MVP, easy to refactor
2. **Strong Consistency**: ACID transactions, sufficient for current scale
3. **Monolithic Architecture**: Right choice for MVP, can split later
4. **No Caching Yet**: Acceptable for MVP, add when needed
5. **Type Safety**: Comprehensive type hints for maintainability
6. **Async Throughout**: Non-blocking I/O for better performance
7. **Pydantic Validation**: Automatic request/response validation
8. **JWT Authentication**: Stateless, scalable
9. **SQLAlchemy ORM**: Abstraction over raw SQL, maintainable
10. **FastAPI Dependencies**: Clean dependency injection

---

## Future Enhancements to Consider

1. **Caching Layer**: Redis for hot data
2. **Message Queue**: For async processing (notifications, analytics)
3. **Full-text Search**: Elasticsearch for listing search
4. **GraphQL**: Alternative to REST for flexible queries
5. **WebSockets**: Real-time updates for swap status
6. **Rate Limiting**: Prevent abuse
7. **API Versioning**: Support multiple API versions
8. **Event Sourcing**: For audit trail and complex state
9. **CQRS**: If read/write patterns diverge significantly
10. **Microservices**: When team/scale requires it

---

## Trade-offs Made

| Decision | Pros | Cons | Alternative |
|----------|------|------|-------------|
| Service Layer | Simple, fast to develop | Less testable | Repository Pattern |
| Monolithic | Easier deployment, simpler | Harder to scale | Microservices |
| No Caching | Simpler codebase | Slower queries | Redis caching |
| Auto-migrations | Quick setup | Not production-ready | Alembic |
| Strong Consistency | Predictable behavior | Slower writes | Eventual consistency |

Each decision was made considering MVP requirements, team size, and future scalability needs.

