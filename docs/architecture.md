# SCMXPertLite Architecture

## High-Level View

```text
User / Browser / Postman
        |
        | HTTPS REST requests
        v
   FastAPI application
        |
        +--> Middleware: request context, auth handling
        |
        +--> Routes: health, auth, admin endpoints
        |
        +--> Services: password hashing, token logic, validation
        |
        +--> Database layer: Motor / MongoDB access
        |
        v
      MongoDB

Optional future path:
FastAPI / services <----> Kafka / event-driven workers
```

## Concepts Covered

- Client-server: the frontend or API client sends requests, and FastAPI returns responses.
- REST: the current API is request/response based, which is simple for CRUD and auth flows.
- WebSocket: useful later if SCMXPertLite needs real-time status updates, notifications, or live dashboards.
- Event-driven systems: useful when actions should trigger asynchronous work such as audit events, notifications, or background processing.

## Request Flow

1. The client sends a request to the FastAPI app.
2. Middleware can prepare request state and handle cross-cutting concerns.
3. The route validates the payload and calls the service layer.
4. The service layer performs password, token, and role logic.
5. The database layer talks to MongoDB.
6. The API returns a structured JSON response.

## Notes for the Day 1 Exercise

- The intern should redraw this architecture on paper to build a mental model.
- The diagram is intentionally simple so it can grow later without changing the core flow.
