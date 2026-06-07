# Security Alerts API - Technical Test

This repository contains a REST API built with FastAPI designed to manage and query security alerts. The project was developed progressively across three exercises, starting from a basic in-memory API and evolving into a robust, database-backed application utilizing Hexagonal Architecture.

The final implementation features asynchronous MongoDB persistence, an immutable SQLite audit log, and external threat enrichment integration. It emphasizes clean code principles, strict separation of concerns, and comprehensive API documentation using OpenAPI standards.

## 2. Architecture & Design Decisions

The application is structured using **Hexagonal Architecture** (Ports and Adapters). This ensures that the core business logic (Domain and Application layers) remains completely isolated from external frameworks, databases, and HTTP clients (Infrastructure layer).

Below are the key design decisions and assumptions made during the resolution of the exercises:

### Exercise 1: In-Memory API & Validation

* **Framework:** Built with FastAPI and Pydantic for fast, asynchronous request handling and automatic OpenAPI schema generation.
* **Alert Status:** The status of a newly created alert is always set to `"new"`.
* **Duplicate Detection:** If an alert with an existing title and source IP is submitted, the system checks the time elapsed. The duplication logic specifically disallows the creation of alerts with the exact same title and IP within 5 minutes of the first one.
* **Tags:** Tags are accepted in the payload and stored, but filtering by tags is not supported in the GET request.
* **Optional Challenge:** Implemented a GET endpoint with cursor-based pagination and filtering by `severity` and `source_ip`, including rich OpenAPI examples.

### Exercise 2: MongoDB Persistence & Hexagonal Architecture

* **Persistence:** Replaced the in-memory store with MongoDB using the asynchronous `motor` driver.
* **Status Updates & Duplication:** To support status updates, a `find_latest_by_title_and_ip` repository method was created. Statuses only transition from `"new"` to `"updated"`. An `updated_at` field was introduced to enforce the 5-minute rule; the duplication logic now checks this new field to determine if an alert can be updated.
* **Optional Challenge:** Implemented optimistic locking. Updates to an alert's status use a `version` field. If a concurrent modification occurs, a `ConflictError` (HTTP 409) is raised.

### Exercise 3: Audit Logging & External Enrichment

* **Audit Logging:** Implemented an immutable SQLite database to record every status change. The `changed_by` field is defaulted to `"system"`.
* **Threat Enrichment:** Two enrichment service adapters were created: a dummy client for testing/fallback and a real client targeting the VirusTotal API. Both use `httpx` and handle timeouts and 5xx retries.
* **Enrichment Response:** When an alert is created or updated via the POST endpoint, the API returns the enriched threat context (`reputation_score`, `categories`, `last_seen`, `country`) directly in the response body.
* **Optional Challenge:** The external threat enrichment call is executed asynchronously in parallel with the MongoDB save operation using `asyncio.gather`. Partial failures are handled gracefully; if the enrichment service times out or fails, the alert is still saved successfully without the enrichment payload.

## 3. Getting Started

### 3.1 Prerequisites

* Python 3.10 or higher
* Pipenv (for managing virtual environments and dependencies)
* Docker and Docker Compose (for running the local MongoDB instance)

### 3.2 Environment Setup

1. **Clone the repository and navigate to the project directory:**
Ensure you are in the root directory where the `Pipfile` is located.
2. **Install dependencies:**
Use Pipenv to install the required packages.
```bash
pipenv install --dev

```


3. **Activate the virtual environment:**
```bash
pipenv shell

```


4. **Set up environment variables:**
Navigate to the latest exercise directory (e.g., `exercise_3`) and copy the environment template.
```bash
cp exercise_3/.env-template exercise_3/.env

```


*Note: Open the newly created `.env` file and add your `VIRUSTOTAL_API_KEY` if you wish to use the real enrichment service instead of the dummy client.*
5. **Start the MongoDB Database:**
Use Docker Compose to spin up the local MongoDB instance.
```bash
cd exercise_3
docker-compose up -d
cd ..

```


6. **Run the Application:**
Start the FastAPI development server:
```bash
fastapi dev exercise_3/main.py

```


Alternatively, you can use Uvicorn directly:
```bash
uvicorn exercise_3.main:app --reload

```


7. **View Documentation:**
Once the server is running, access the interactive API documentation at:
* Swagger UI: `http://127.0.0.1:8000/docs`



## 4. Testing

The project includes a comprehensive automated test suite utilizing `pytest` and `pytest-asyncio`.

* **Unit Tests:** Business logic is tested using mocked repository and service layers.
* **Database Tests:** The MongoDB repository is tested using a custom in-memory FakeCollection pattern to ensure logic is verified without requiring a live database connection.
* **Integration Tests:** * The SQLite audit log is tested against a real in-memory SQLite connection to validate schemas and constraints.
* The REST HTTP clients are tested using `httpx.MockTransport` to simulate timeouts, server errors, retry logic, and successful data parsing without making actual network requests.



To run the entire test suite, execute the following command:

```bash
pytest

```

To view detailed output for a specific exercise, run:

```bash
pytest -v exercise_3/tests/

```

## 5. Project Structure

The project evolves from a standard layered architecture in Exercise 1 into a strict Hexagonal Architecture in Exercises 2 and 3.

### Root Level

```text
classora-technical-test/
├── .gitignore
├── Pipfile              # Virtual environment and dependencies management
└── Pipfile.lock

```

### Exercise 1: Standard Layered Architecture

This exercise establishes the basic API and validation logic without external persistence.

```text
exercise_1/
├── README.md
├── main.py              # FastAPI application initialization
├── routers/
│   └── alerts.py        # API endpoints
├── schemas.py           # Pydantic validation models
├── services.py          # In-memory database and core logic
└── tests/
    ├── test_alert_service.py
    └── test_api_endpoints.py

```

### Exercise 2: Hexagonal Architecture & MongoDB

This exercise introduces Ports and Adapters, separating domain logic from the MongoDB infrastructure.

```text
exercise_2/
├── .env-template
├── README.md
├── docker-compose.yml   # MongoDB container configuration
├── main.py              # FastAPI application initialization
├── config.py            # Environment variables configuration
├── dependencies.py      # Dependency injection container
├── domain/              # Inner Hexagon: Pure Python business rules
│   ├── exceptions.py
│   ├── filters.py
│   ├── models.py
│   └── ports.py         # Interfaces for repositories
├── application/         # Application Services: Orchestration
│   └── services.py
├── infrastructure/      # Outer Hexagon: Frameworks and DBs
│   ├── api/
│   │   ├── routers/
│   │   │   └── alerts.py
│   │   └── schemas.py
│   └── database/
│       └── repository.py # MongoDB (Motor) adapter
└── tests/
    ├── test_alert_service.py
    ├── test_api_endpoints.py
    └── test_mongo_repository.py

```

### Exercise 3: Full Architecture with Audit & External API

This exercise builds upon the hexagonal structure, adding an audit log database and external HTTP clients.

```text
exercise_3/
├── .env-template
├── README.md
├── docker-compose.yml   # MongoDB container configuration
├── main.py              # FastAPI app with startup events (lifespan)
├── config.py            # Configuration including SQLite path and API keys
├── dependencies.py      # Dependency injection container
├── domain/              # Inner Hexagon: Pure Python business rules
│   ├── exceptions.py    # Added EnrichmentError
│   ├── filters.py
│   ├── models.py        # Added AuditLogEntry and EnrichmentData
│   └── ports.py         # Added AuditLogRepository and ThreatEnrichmentService
├── application/         # Application Services: Orchestration
│   └── services.py      # Orchestrates DB saves and parallel enrichment calls
├── infrastructure/      # Outer Hexagon: Frameworks, DBs, and APIs
│   ├── api/
│   │   ├── routers/
│   │   │   └── alerts.py
│   │   └── schemas.py
│   ├── database/
│   │   ├── audit_repository.py # SQLite adapter for immutable logs
│   │   └── repository.py       # MongoDB adapter
│   └── external/               # Third-party integrations
│       ├── dummy_threat_client.py
│       └── virustotal_client.py
└── tests/
    ├── test_alert_service.py
    ├── test_api_endpoints.py
    ├── test_audit_log.py       # Integration tests for SQLite
    ├── test_mongo_repository.py
    └── test_threat_client.py   # Tests using httpx.MockTransport

```

## 6. Author

**Name:** Miquel Vives Marcus

**Contact:** miquelvm2000@gmail.com