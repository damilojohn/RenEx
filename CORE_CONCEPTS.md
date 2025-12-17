# Core Concepts Applied in RenEx Backend Implementation

This document explains the key software engineering concepts used in building this FastAPI backend, designed for junior developers.

## 1. **Layered Architecture (Separation of Concerns)**

### What it is:
We organized code into distinct layers, each with a specific responsibility.

### Structure:
```
Models (Database Layer) → Service (Business Logic) → Views (API Layer)
```

### Why it matters:
- **Models** (`models.py`): Define database structure and relationships
- **Services** (`service.py`): Contain business logic and data operations
- **Views** (`views.py`): Handle HTTP requests/responses and route to services
- **Schemas** (`schemas.py`): Define data validation and serialization

### Example:
```python
# Model: Database structure
class Listings(RecordModel):
    volume: Mapped[float]
    price: Mapped[float]

# Service: Business logic
async def create_listing(...):
    # Validation, business rules
    new_listing = Listings(...)
    session.add(new_listing)

# View: HTTP endpoint
@base_router.post("/listings/")
async def create_new_listing(...):
    result = await create_listing(...)
    return JSONResponse(...)
```

---

## 2. **Object-Relational Mapping (ORM) with SQLAlchemy**

### What it is:
Instead of writing raw SQL, we use Python objects that represent database tables.

### Key Concepts:

#### **Models as Python Classes**
```python
class Listings(RecordModel):
    __tablename__ = "listings"
    volume: Mapped[float] = mapped_column(Float(), nullable=False)
```
- Each class = a database table
- Each attribute = a column
- `Mapped[type]` = type hinting for the column

#### **Relationships**
```python
# One-to-Many: One user has many listings
user = relationship("RenExUser", back_populates="listings")

# Foreign Keys: Link tables together
user_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id", ondelete="cascade")
)
```

#### **Querying with ORM**
```python
# Instead of: SELECT * FROM listings WHERE user_id = ?
# We write:
result = await session.execute(
    select(Listings).filter(Listings.user_id == user_id)
)
```

---

## 3. **Asynchronous Programming (Async/Await)**

### What it is:
Allows the server to handle multiple requests concurrently without blocking.

### Key Concepts:

#### **Async Functions**
```python
async def create_listing(...):  # async keyword
    await session.commit()       # await keyword
```

#### **Why Async?**
- **Synchronous**: Request 1 blocks → Request 2 waits → Request 3 waits
- **Asynchronous**: Request 1 waits for DB → Request 2 processes → Request 3 processes

#### **Async Database Operations**
```python
# All database operations are async
await session.execute(query)
await session.commit()
await session.refresh(object)
```

---

## 4. **Dependency Injection**

### What it is:
Instead of creating dependencies inside functions, we "inject" them as parameters.

### Example:
```python
# FastAPI automatically provides these dependencies
async def create_listing(
    user: CurrentUser = Depends(get_current_user),  # Injected!
    session: AsyncSession = Depends(get_db_session)  # Injected!
):
    # user and session are automatically provided
```

### Benefits:
- **Testability**: Easy to mock dependencies
- **Reusability**: Same dependency used across multiple endpoints
- **Separation**: Business logic doesn't create its own dependencies

### Common Dependencies:
- `get_current_user`: Validates JWT token and returns user
- `get_db_session`: Provides database connection
- Both are created once and reused

---

## 5. **Data Validation with Pydantic**

### What it is:
Automatic validation and serialization of request/response data.

### Request Validation:
```python
class ListingCreateRequest(BaseModel):
    volume: float = Field(..., gt=0)  # Must be > 0
    price: float = Field(..., gt=0)    # Must be > 0
    location: str = Field(..., min_length=1, max_length=500)
```

### What Pydantic Does:
1. **Validates** incoming data matches the schema
2. **Converts** types automatically (string → int, etc.)
3. **Rejects** invalid data with clear error messages
4. **Serializes** Python objects to JSON

### Example:
```python
# FastAPI automatically validates the request body
@base_router.post("/listings/")
async def create_listing(
    listing_data: ListingCreateRequest  # Validated automatically!
):
    # listing_data is guaranteed to be valid
```

---

## 6. **RESTful API Design**

### What it is:
Standard way of designing web APIs using HTTP methods and status codes.

### HTTP Methods:
- **GET**: Retrieve data (read-only)
- **POST**: Create new resources
- **PUT**: Update existing resources
- **DELETE**: Remove resources

### Status Codes:
```python
status.HTTP_200_OK          # Success
status.HTTP_201_CREATED     # Resource created
status.HTTP_400_BAD_REQUEST # Invalid input
status.HTTP_404_NOT_FOUND   # Resource not found
status.HTTP_401_UNAUTHORIZED # Not authenticated
```

### RESTful Endpoints:
```
GET    /listings/          # Get all listings
POST   /listings/          # Create listing
GET    /listings/{id}      # Get specific listing
PUT    /listings/{id}      # Update listing
DELETE /listings/{id}      # Delete listing
```

---

## 7. **Authentication & Authorization**

### JWT (JSON Web Tokens):
```python
# Token contains user ID
token = jwt.encode({"sub": str(user.id)}, key=SECRET_KEY)

# Token is validated on each request
user_id = verify_access_token(token)
```

### Flow:
1. User logs in → Server creates JWT token
2. Client stores token (localStorage, cookies)
3. Client sends token in `Authorization: Bearer <token>` header
4. Server validates token → Extracts user ID
5. Server uses user ID for authorization

### Authorization:
```python
# Only listing owner can update
if listing.user_id != user.id:
    raise HTTPException(403, "Permission denied")
```

---

## 8. **Database Transactions**

### What it is:
A group of database operations that either all succeed or all fail.

### Example:
```python
try:
    session.add(new_listing)
    session.add(related_data)
    await session.commit()  # All changes saved together
except Exception:
    await session.rollback()  # All changes reverted
    raise
```

### Why it matters:
- **Data integrity**: Prevents partial updates
- **Consistency**: Database stays in valid state
- **Error recovery**: Can undo all changes if something fails

---

## 9. **Error Handling**

### HTTP Exceptions:
```python
if not listing:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Listing not found"
    )
```

### Try-Except Blocks:
```python
try:
    # Risky operation
    await session.commit()
except Exception as e:
    await session.rollback()  # Cleanup
    raise HTTPException(500, f"Error: {str(e)}")
```

### Best Practices:
- **Specific errors**: Use appropriate HTTP status codes
- **Clear messages**: Help frontend understand what went wrong
- **Rollback**: Always rollback database changes on error
- **Logging**: Log errors for debugging (not shown in response)

---

## 10. **Type Hints**

### What it is:
Specifying the expected types of variables and function parameters.

### Example:
```python
def create_listing(
    listing_data: ListingCreateRequest,  # Type hint
    user_id: UUID,                        # Type hint
    session: AsyncSession                 # Type hint
) -> ListingResponse:                    # Return type hint
    ...
```

### Benefits:
- **IDE Support**: Autocomplete, error detection
- **Documentation**: Code is self-documenting
- **Type Checking**: Tools can catch type errors before runtime
- **Refactoring**: Easier to safely change code

---

## 11. **Query Filtering & Pagination**

### Filtering:
```python
query = select(Listings).filter(
    and_(
        Listings.user_id != user_id,
        Listings.status == "active",
        Listings.energy_type == energy_type
    )
)
```

### Pagination:
```python
offset = (page - 1) * page_size
query = query.limit(page_size).offset(offset)
```

### Why it matters:
- **Performance**: Don't load all data at once
- **User Experience**: Faster responses, manageable data
- **Scalability**: Works with large datasets

---

## 12. **Enums for Type Safety**

### What it is:
Predefined set of allowed values.

### Example:
```python
class ListingType(str, Enum):
    demand = "demand"
    supply = "supply"

# Usage
listing_type: ListingType = ListingType.supply
```

### Benefits:
- **Type Safety**: Can't use invalid values
- **IDE Support**: Autocomplete shows all options
- **Validation**: Pydantic validates enum values automatically
- **Refactoring**: Change enum value in one place

---

## 13. **Database Relationships**

### One-to-Many:
```python
# One User has many Listings
class RenExUser(RecordModel):
    listings = relationship("Listings", back_populates="user")

class Listings(RecordModel):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user = relationship("RenExUser", back_populates="listings")
```

### Cascade Deletes:
```python
ForeignKey("users.id", ondelete="cascade")
# When user is deleted, their listings are automatically deleted
```

### Accessing Related Data:
```python
# Get user's listings
user.listings  # Returns all listings for this user

# Get listing's user
listing.user   # Returns the user who owns this listing
```

---

## 14. **Request/Response Models (Schemas)**

### Request Models:
```python
class ListingCreateRequest(BaseModel):
    volume: float
    price: float
    # Only fields user can send
```

### Response Models:
```python
class ListingResponse(BaseModel):
    id: UUID
    volume: float
    created_at: datetime
    # Only fields user should see
```

### Why separate models?
- **Security**: Don't expose internal fields (password hashes, etc.)
- **Validation**: Different rules for input vs output
- **Versioning**: Can change request/response independently
- **Documentation**: Auto-generated API docs show exact structure

---

## 15. **Router Organization**

### What it is:
Grouping related endpoints together.

### Structure:
```python
# Each module has its own router
base_router = APIRouter(prefix="/listings", tags=["Listings"])

# All endpoints in this file share the prefix
@base_router.post("/")  # Becomes /listings/
@base_router.get("/me")  # Becomes /listings/me
```

### Main Router:
```python
# main.py includes all routers
app.include_router(listings_router)
app.include_router(swaps_router)
app.include_router(auth_router)
```

### Benefits:
- **Organization**: Related endpoints grouped together
- **Maintainability**: Easy to find and modify endpoints
- **Modularity**: Can add/remove entire modules easily

---

## 16. **Environment Configuration**

### What it is:
Storing configuration (secrets, database URLs) outside of code.

### Settings Class:
```python
class Settings(BaseSettings):
    DB_CONNECTION_STRING: str
    JWT_SECRET_KEY: str
    JWT_EXP: int
```

### Usage:
```python
settings = get_settings()
connection = settings.DB_CONNECTION_STRING
```

### Why it matters:
- **Security**: Secrets not in code (use .env file)
- **Flexibility**: Different configs for dev/staging/prod
- **Best Practice**: Never hardcode secrets

---

## Summary: Key Takeaways for Juniors

1. **Separation of Concerns**: Each file has one job
2. **Type Safety**: Use type hints everywhere
3. **Validation**: Validate all inputs with Pydantic
4. **Error Handling**: Always handle errors gracefully
5. **Async**: Use async/await for I/O operations
6. **Transactions**: Group related DB operations
7. **RESTful**: Follow REST conventions
8. **Security**: Validate authentication on protected routes
9. **Documentation**: Code should be self-documenting
10. **Testing**: Structure code to be testable (dependency injection helps)

---

## Next Steps for Learning

1. **Practice**: Try adding a new endpoint following these patterns
2. **Debug**: Add logging to see how data flows
3. **Test**: Write unit tests for services
4. **Read**: Study FastAPI and SQLAlchemy documentation
5. **Experiment**: Try breaking things and fixing them

