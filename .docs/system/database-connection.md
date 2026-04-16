# Backend–Database Connection (SQLAlchemy Async + asyncpg)

## 1. Overview

This backend connects to PostgreSQL (Supabase) using **SQLAlchemy in async mode** with the **asyncpg driver**.

The goal is not just to "connect to a database", but to ensure:

* non-blocking I/O
* architectural coherence with FastAPI
* predictable behavior under concurrency
* clean separation of concerns

---

## 2. Connection Stack

The connection is composed of three layers:

### 2.1 SQLAlchemy (ORM / Core)

SQLAlchemy provides:

* data modeling (tables, schemas)
* query construction
* session and transaction management
* abstraction from raw SQL and drivers

It does **not** connect directly to PostgreSQL.

---

### 2.2 Async Engine (SQLAlchemy asyncio extension)

The backend uses:

```python
from sqlalchemy.ext.asyncio import create_async_engine
```

This creates an **AsyncEngine**, which:

* integrates with `asyncio`
* allows `await`-based database operations
* ensures DB calls do not block the event loop

---

### 2.3 asyncpg (Driver)

The actual connection to PostgreSQL is handled by **asyncpg**.

It is a high-performance PostgreSQL driver designed for asyncio, using:

* binary protocol
* asynchronous network I/O

SQLAlchemy communicates with PostgreSQL through asyncpg using the dialect:

```
postgresql+asyncpg://
```

---

## 3. Connection String

Example:

```
postgresql+asyncpg://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres?ssl=require
```

### Key elements

* `postgresql+asyncpg://` → defines SQLAlchemy dialect + driver
* `db.xxx.supabase.co` → direct Supabase host (IPv6-compatible)
* `5432` → standard PostgreSQL port
* `ssl=require` → required by Supabase

---

## 4. Why Async is Used

This system is **I/O-bound**, not CPU-bound.

The backend performs:

* HTTP request handling
* database reads/writes
* external API calls (LLMs, enrichment)

Most time is spent waiting on I/O.

Using async ensures:

* the event loop is not blocked during DB calls
* multiple requests can progress concurrently
* system throughput improves under load

---

## 5. Architectural Coherence

The backend is built on FastAPI (ASGI), which is async-first.

To maintain consistency:

| Layer           | Model |
| --------------- | ----- |
| API (FastAPI)   | async |
| Business logic  | async |
| External APIs   | async |
| Database access | async |

Mixing sync DB access into an async system introduces:

* threadpool overhead
* hidden blocking
* increased complexity

---

## 6. Session Management

Sessions must be async-aware.

Typical pattern:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

Usage:

```python
async with SessionLocal() as session:
    result = await session.execute(query)
```

---

## 7. Concurrency Model

The system uses:

* asyncio tasks
* bounded concurrency (semaphores)
* async pipelines

Database access must follow the same model to avoid becoming a bottleneck.

If DB access were synchronous:

* each query would block execution
* concurrency benefits would collapse

---

## 8. Supabase-Specific Considerations

### Direct connection vs Pooler

This system uses **direct connection**:

```
db.xxx.supabase.co:5432
```

Reason:

* Fly.io supports IPv6
* direct connection is recommended for persistent backends

Avoid:

* transaction pooler (port 6543) with asyncpg

Because:

* it does not support prepared statements
* asyncpg relies on them internally

---

## 9. Common Failure Points

### Incorrect dialect

Using:

```
postgresql://
```

instead of:

```
postgresql+asyncpg://
```

---

### Mixing sync and async

Examples:

* using `create_engine()` instead of `create_async_engine()`
* using `Session` instead of `AsyncSession`
* missing `await` in DB calls

---

### SSL issues

Supabase requires:

```
?ssl=require
```

---

### Pool misconfiguration

Missing parameters like:

* `pool_pre_ping=True`
* `pool_recycle`

can cause stale connections in production

---

## 10. Design Principle

The database is treated as:

> a critical external dependency with deterministic access rules

Not as a passive storage layer.

This means:

* all inputs are validated before persistence
* all writes are controlled
* failures are explicit

---

## 11. Summary

This connection model is chosen because it:

* aligns with FastAPI async architecture
* avoids blocking under I/O
* supports controlled concurrency
* integrates cleanly with Supabase over IPv6

It is not an optimization choice.

It is an architectural requirement for system coherence.