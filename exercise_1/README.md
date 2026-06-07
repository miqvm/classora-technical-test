# Exercise 1 - Security Alerts API

This repository contains a REST API built with FastAPI designed to manage and query security alerts. It implements robust data validation using Pydantic, comprehensive OpenAPI documentation, and an in-memory thread-safe database for duplicate detection.

The optional challenge has been completed: the API includes a GET endpoint with filtering, cursor-based pagination, and rich OpenAPI examples for different filtering combinations.

## Features

* **FastAPI & Pydantic**: Fast, asynchronous endpoints with automatic request validation and type enforcement.
* **OpenAPI Standards**: Fully documented schemas, query parameters, constraints, and rich examples for success and error responses.
* **Duplicate Detection**: Thread-safe, in-memory validation that rejects duplicate alerts (same `title` and `source_ip`) created within a 5-minute rolling window.
* **Advanced Querying (Optional Challenge)**: A GET endpoint supporting cursor-based pagination and filtering by severity and source IP address.

## Prerequisites

* Python (Version as specified in the Pipfile, 3.10+ recommended)
* Pipenv (for managing virtual environments and dependencies)

## Installation

1. Navigate to the project directory where the `Pipfile` is located.
2. Install the dependencies using Pipenv:
```bash
pipenv install --dev

```


3. Activate the virtual environment:
```bash
pipenv shell

```



## Running the Application

You can start the FastAPI development server using the FastAPI CLI (which is included with the `standard` extras):

```bash
fastapi dev exercise_1/main.py

```

Alternatively, using Uvicorn directly:

```bash
uvicorn exercise_1.main:app --reload

```

Once the server is running, you can view the automatically generated interactive OpenAPI documentation at:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

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

* `201 Created`: Alert successfully created. Returns the alert details including an auto-generated `alert_id` (UUID), `status`, and `created_at` timestamp.
* `409 Conflict`: Returned if an alert with the exact same `title` and `source_ip` was submitted in the last 5 minutes.
* `422 Unprocessable Entity`: Returned if the request body fails Pydantic validation (e.g., invalid IP address, missing fields).

### 2. List Security Alerts (Optional Challenge)

**GET** `/api/v1/alerts`

Retrieves a paginated list of security alerts sorted by creation time (newest first).

**Query Parameters**:

* `severity` (string, optional): Filter alerts by severity level (`low`, `medium`, `high`, `critical`).
* `source_ip` (string, optional): Filter alerts by source IP. Formats are automatically canonicalized for accurate matching.
* `limit` (integer, optional): Maximum number of alerts to return (between 1 and 100). Defaults to 10.
* `cursor` (string, optional): Base64-encoded string pointing to the next page of results.

**Responses**:

* `200 OK`: Returns a list of matching alerts and a `pagination` object containing the `next_cursor`, `limit`, and `total` count of records matching the filters.
* `422 Unprocessable Entity`: Validation error on the query parameters.

*Note: The Swagger UI (`/docs`) includes multiple examples demonstrating how the API behaves with no filters, filtering by severity, filtering by source IP, combined filtering, and cursor usage.*

## Running the Tests

The project includes an automated test suite using `pytest` and `pytest-asyncio` to test the in-memory database logic, duplicate checks, filtering, pagination, and API endpoint validations.

To run the tests, execute the following command from the root directory:

```bash
pytest exercise_1/tests/

```

To see more detailed output, you can run:

```bash
pytest -v exercise_1/tests/

```