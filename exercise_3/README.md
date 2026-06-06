# Exercise 3 - Security Alerts API (Hexagonal Architecture, MongoDB, Audit & Enrichment)

This repository contains a REST API built with FastAPI designed to manage and query security alerts. Building upon the foundation of Exercises 1 and 2, this version maintains the Hexagonal Architecture and MongoDB persistence, while introducing an immutable SQLite audit log for status changes and an external REST client for threat context enrichment.

The optional challenge for this exercise has been successfully completed: the external threat enrichment call is asynchronous and runs in parallel with the MongoDB save operation using `asyncio.gather`. The system handles partial failures gracefully, ensuring that a failed enrichment does not prevent the alert from being saved.

---

## Features

* **Hexagonal Architecture**: Strict separation of concerns divided into Domain, Application, and Infrastructure layers.
* **MongoDB Persistence**: Asynchronous database operations using Motor, with indexing for fast querying and duplicate detection.
* **SQLite Audit Logging**: An immutable audit trail in a SQL database that records every status change of an alert, complete with timestamps and responsible actors.
* **External Threat Enrichment**: A REST client built with `httpx` that fetches threat context (reputation score, categories, last seen, country) based on the source IP. It includes a 3-second timeout, handles 5xx retries automatically, and raises specific `EnrichmentError` exceptions.
* **Parallel Async Execution (Optional Challenge)**: The system fetches enrichment data concurrently with the database save operation. If the enrichment service is unavailable, the alert is still successfully saved to ensure system resilience.
* **Optimistic Locking**: Updates to alert status use a version field to prevent race conditions and raise a conflict error upon concurrent modifications.
* **FastAPI & OpenAPI Standards**: Fully documented schemas, automatic request validation, and rich examples for success and error responses.

---

## Prerequisites

* Python (Version as specified in the Pipfile, 3.10+ recommended)
* Pipenv (for managing virtual environments and dependencies)
* Docker & Docker Compose (for running the local MongoDB instance)
* SQLite (Included in the Python standard library)

---

## Installation and Setup

1. Navigate to the project directory where the `Pipfile` is located.
2. Install the dependencies using Pipenv:

```bash
pipenv install --dev

```

3. Activate the virtual environment:

```bash
pipenv shell

```

4. Set up the environment variables by copying the provided template:

```bash
cp exercise_3/.env-template exercise_3/.env

```

5. Start the MongoDB database using Docker Compose:

```bash
cd exercise_3
docker-compose up -d
cd ..

```

---

## Running the Application

You can start the FastAPI development server using the FastAPI CLI:

```bash
fastapi dev exercise_3/main.py

```

Alternatively, using Uvicorn directly:

```bash
uvicorn exercise_3.main:app --reload

```

Once the server is running, view the automatically generated interactive OpenAPI documentation at:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

---

## Project Structure

The codebase is organized following Hexagonal Architecture principles:

* `domain/`: Contains business models (`Alert`, `Page`), audit schemas, custom exceptions (`EnrichmentError`), and port interfaces for both the database repositories and the enrichment client.
* `application/`: Contains the core orchestration services, managing the parallel execution of the MongoDB save and the enrichment fetch.
* `infrastructure/`: Contains external adapters.
* `api/`: FastAPI routers and Pydantic schemas for HTTP requests/responses.
* `database/`: MongoDB implementation of the repository port and SQLite adapter for the audit log.
* `clients/`: HTTP client adapters integrating with the external threat intelligence service.

---

## API Endpoints

### 1. Create a Security Alert

**POST** `/api/v1/alerts`

Registers a security alert event. The system validates the payload, checks for recent duplicates, fetches threat context in parallel, and logs the initial status creation in the SQLite audit log.

**Request Body (JSON)**:

* `title` (string, required): 3 to 120 characters.
* `severity` (string, required): Must be one of `low`, `medium`, `high`, or `critical`.
* `source_ip` (string, required): A valid IPv4 or IPv6 address.
* `description` (string, required): Maximum 2000 characters.
* `tags` (list[string], optional): Maximum of 10 items.

**Responses**:

* `201 Created`: Alert successfully created or updated. Returns the alert details, including enrichment data if the external service was available.
* `409 Conflict`: Returned if an alert with the exact same `title` and `source_ip` was submitted in the last 5 minutes, or if an optimistic locking version mismatch occurs during an update.
* `422 Unprocessable Entity`: Returned if the request body fails Pydantic validation.

### 2. List Security Alerts

**GET** `/api/v1/alerts`

Retrieves a paginated list of security alerts stored in MongoDB, sorted by creation time (newest first).

**Query Parameters**:

* `severity` (string, optional): Filter alerts by severity level.
* `source_ip` (string, optional): Filter alerts by source IP.
* `limit` (integer, optional): Maximum number of alerts to return (between 1 and 100). Defaults to 10.
* `cursor` (string, optional): ISO-8601 formatted timestamp string pointing to the next page of results.

**Responses**:

* `200 OK`: Returns a list of matching alerts and a `pagination` object containing the `next_cursor`, `limit`, and `total` count.
* `422 Unprocessable Entity`: Validation error on the query parameters.

---

## Running the Tests

The project includes an automated test suite using `pytest` and `pytest-asyncio`. It features comprehensive unit and integration tests. The SQLite audit log is tested against a real in-memory connection to ensure schema and constraints are respected. The REST client is tested using mocked HTTP transports (e.g., `respx` or `httpx.MockTransport`) to simulate timeouts, 5xx retries, and successful enrichment payloads.

To run the tests, execute the following command from the root directory:

```bash
pytest exercise_3/tests/

```

To see more detailed output, run:

```bash
pytest -v exercise_3/tests/

```