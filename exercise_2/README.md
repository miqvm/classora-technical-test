# Exercise 2 - Security Alerts API (Hexagonal Architecture & MongoDB)

This repository contains a REST API built with FastAPI designed to manage and query security alerts. Building upon the foundation of Exercise 1, this version introduces Hexagonal Architecture for a clean separation of concerns and replaces the in-memory store with a persistent MongoDB database layer.

The optional challenge has been successfully completed: the API implements optimistic locking on alert status updates using a version field to prevent race conditions. The API also retains the GET endpoint with filtering, cursor-based pagination, and rich OpenAPI examples.

## Features

* **Hexagonal Architecture**: Strict separation of concerns divided into Domain (core models and ports), Application (business logic services), and Infrastructure (FastAPI routers, MongoDB adapters).
* **MongoDB Persistence**: Asynchronous database operations using the Motor engine, complete with proper indexing for fast querying and duplicate detection.
* **FastAPI & Pydantic**: Fast, asynchronous endpoints with automatic request validation and type enforcement.
* **OpenAPI Standards**: Fully documented schemas, query parameters, constraints, and rich examples for success and error responses.
* **Duplicate Detection & Optimistic Locking (Optional Challenge)**:
* Rejects duplicate alerts (same `title` and `source_ip`) created within a 5-minute rolling window with a `409 Conflict`.
* If the same alert occurred older than 5 minutes ago, it updates the alert's status securely using optimistic locking via a `version` field, raising a conflict error if a concurrent modification occurs.


* **Advanced Querying**: A GET endpoint supporting cursor-based pagination and filtering by severity and source IP address.

## Prerequisites

* Python (Version as specified in the Pipfile, 3.10+ recommended)
* Pipenv (for managing virtual environments and dependencies)
* Docker & Docker Compose (for running the local MongoDB instance)

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

4. Set up the environment variables:
Copy the provided `.env-template` to a new file named `.env` in the `exercise_2` directory.

```bash
cp exercise_2/.env-template exercise_2/.env

```

5. Start the MongoDB database using Docker Compose:

```bash
cd exercise_2
docker-compose up -d
cd ..

```

## Running the Application

You can start the FastAPI development server using the FastAPI CLI:

```bash
fastapi dev exercise_2/main.py

```

Alternatively, using Uvicorn directly:

```bash
uvicorn exercise_2.main:app --reload

```

Once the server is running, you can view the automatically generated interactive OpenAPI documentation at:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

## Project Structure

The codebase is organized following Hexagonal Architecture principles:

* `domain/`: Contains business models (`Alert`, `Page`), filters, custom exceptions, and port interfaces (`AlertRepository`). No external framework dependencies reside here.
* `application/`: Contains the `AlertService` which orchestrates business use cases (creation, duplicate validation, fetching) using domain ports.
* `infrastructure/`: Contains external adapters.
* `api/`: FastAPI routers and Pydantic schemas for HTTP requests/responses.
* `database/`: MongoDB implementation of the repository port (`MongoAlertRepository`).



## API Endpoints

### 1. Create a Security Alert

**POST** `/api/v1/alerts`

Registers a security alert event. Validates that the payload is well-formed and checks for recent duplicates.

**Request Body (JSON)**:

* `title` (string, required): 3 to 120 characters.
* `severity` (string, required): Must be one of `low`, `medium`, `high`, or `critical`.
* `source_ip` (string, required): A valid IPv4 or IPv6 address.
* `description` (string, required): Maximum 2000 characters.
* `tags` (list[string], optional): Maximum of 10 items.

**Responses**:

* `201 Created`: Alert successfully created or updated. Returns the alert details including an auto-generated `alert_id` (UUID), `status`, `created_at`, `updated_at`, and the current `version`.
* `409 Conflict`: Returned if an alert with the exact same `title` and `source_ip` was submitted in the last 5 minutes, or if an optimistic locking version mismatch occurs during an update.
* `422 Unprocessable Entity`: Returned if the request body fails Pydantic validation (e.g., invalid IP address, missing fields).

### 2. List Security Alerts

**GET** `/api/v1/alerts`

Retrieves a paginated list of security alerts stored in MongoDB, sorted by creation time (newest first).

**Query Parameters**:

* `severity` (string, optional): Filter alerts by severity level (`low`, `medium`, `high`, `critical`).
* `source_ip` (string, optional): Filter alerts by source IP. Formats are automatically canonicalized for accurate matching.
* `limit` (integer, optional): Maximum number of alerts to return (between 1 and 100). Defaults to 10.
* `cursor` (string, optional): ISO-8601 formatted timestamp string pointing to the next page of results.

**Responses**:

* `200 OK`: Returns a list of matching alerts and a `pagination` object containing the `next_cursor`, `limit`, and `total` count of records matching the filters in the current page.
* `422 Unprocessable Entity`: Validation error on the query parameters.

## Running the Tests

The project includes an automated test suite using `pytest` and `pytest-asyncio`. The tests cover the business logic via mocked services and test the MongoDB repository logic using an isolated fake memory collection pattern to ensure fast and reliable execution without requiring a live database connection during unit testing.

To run the tests, execute the following command from the root directory:

```bash
pytest exercise_2/tests/

```

To see more detailed output, you can run:

```bash
pytest -v exercise_2/tests/

```