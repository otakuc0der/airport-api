# Airport API

Backend REST API for managing airports, airplanes, routes, scheduled flights, ticket reservations, and customer orders.

The project is built with **Django** and **Django REST Framework** and models the complete airport booking workflow. It includes a custom authentication system, an optimized Django Administration panel, realistic demo data generation, and a well-structured relational database.

> [!NOTE]
> The REST API is currently under active development.
>
> The current implementation focuses on the project architecture, database design, Django Admin customization, and demo data generation. API endpoints, JWT authentication, Swagger documentation, and Docker support will be added in the following development stages.

---

# Overview

Airport API simulates the backend of a real-world airport reservation system.

The project allows administrators to manage airports, airplanes, routes, scheduled flights, crews, customers, ticket reservations, and booking orders while maintaining data consistency through database constraints and model validation.

The application follows Django best practices, uses UUID primary keys for all airport domain models, and is designed to be easily extendable with additional business logic.

---

# Features

The current implementation provides:

- Custom User model with email authentication
- UUID primary keys for airport domain models
- Airport, city and country management
- Airplane and airplane type management
- Flight crew management
- Route management
- Flight scheduling
- Ticket reservation models
- Customer orders
- Automatic seat capacity calculation
- Flight duration calculation
- Model validation
- Database constraints
- Customized Django Admin
- Optimized admin querysets
- Custom admin filters
- Demo fixture generation
- Environment-based configuration

---

# Database Models

The project currently consists of the following domain models.

---

## User

A custom authentication model based on Django's `AbstractUser`.

### Main features

- Email is used instead of username
- Compatible with Django authentication system
- Supports staff and superuser permissions
- Can create multiple orders

### Relationships

```
User
 └── 1 → N Order
```

---

## Country

Represents a country.

### Main features

- UUID primary key
- Unique country name
- Protected from deletion while related cities exist

### Relationships

```
Country
 └── 1 → N City
```

---

## City

Represents a city.

Each city belongs to exactly one country.

### Validation

- City names must be unique inside the same country.

### Relationships

```
Country
 └── City
        └── 1 → N Airport
```

---

## Airport

Represents an airport.

Each airport is connected to the closest major city.

### Main features

- UUID primary key
- Unique airport name
- Optional image
- Used as both route source and destination

### Relationships

```
City
 └── Airport

Airport
 ├── 1 → N Route (source)
 └── 1 → N Route (destination)
```

---

## Airplane Type

Represents an airplane model.

Examples:

- Boeing 737-800
- Airbus A320neo
- Embraer E195-E2

### Relationships

```
AirplaneType
 └── 1 → N Airplane
```

---

## Airplane

Represents a physical aircraft.

### Stored information

- Unique aircraft name
- Number of rows
- Seats per row
- Airplane type
- Optional image

### Automatic calculations

The total passenger capacity is calculated automatically.

```
capacity = rows × seats_in_row
```

### Relationships

```
AirplaneType
      │
      ▼
Airplane
      │
      └── 1 → N Flight
```

---

## Crew

Represents flight crew members.

Each crew member may participate in multiple scheduled flights.

### Relationships

```
Crew
    N ↔ N
      Flight
```

---

## Route

Represents a route between two airports.

### Stored information

- Source airport
- Destination airport
- Flight distance

### Validation

The project prevents:

- identical source and destination airports
- duplicate source/destination pairs

For example:

```
Kyiv → Warsaw
```

is allowed,

while

```
Kyiv → Kyiv
```

is rejected.

Reverse routes are considered different routes.

```
Kyiv → Warsaw
Warsaw → Kyiv
```

---

## Flight

Represents a scheduled flight.

### Stored information

- Route
- Airplane
- Crew
- Departure time
- Arrival time

### Automatic calculations

```
flight_duration = arrival_time − departure_time
```

### Validation

Arrival time must always be later than departure time.

### Relationships

```
Route
   │
   ▼
Flight
 ├── N ↔ N Crew
 ├── 1 → N Ticket
 └── N → 1 Airplane
```

---

## Order

Represents a customer's booking.

Each order belongs to one user and contains one or more tickets.

### Stored information

- Customer
- Creation date
- Purchased tickets

### Relationships

```
User
  │
  ▼
Order
  │
  └── 1 → N Ticket
```

---

## Ticket

Represents a reserved seat for a particular flight.

### Stored information

- Flight
- Order
- Row
- Seat number

### Validation

The project validates:

- seat row exists
- seat number exists
- duplicate seat reservations are not allowed

Each seat can be booked only once per flight.

---

# Database Diagram

The following diagram illustrates the current database structure and relationships between all project models.

<p align="center">
    <img src="docs/database-diagram.png" width="900">
</p>

The diagram includes:

- entity relationships
- cardinalities
- UUID primary keys
- many-to-many relations
- foreign key dependencies

---

# Technologies

| Technology | Purpose |
|------------|---------|
| Python 3.14 | Programming language |
| Django | Web framework |
| Django REST Framework | REST API |
| SQLite | Development database |
| Pillow | Image handling |
| django-filter | API filtering |
| drf-spectacular | OpenAPI / Swagger |
| Simple JWT | Authentication |
| uv | Dependency management |
| Black | Code formatting |
| Flake8 | Static analysis |
| pytest | Testing |

> **Note**
>
> Some packages (such as Swagger, JWT, and pytest) are already installed but will be fully utilized in later development stages.

# Local Installation

Follow the steps below to run the project locally.

---

## 1. Clone the Repository

Clone the project from GitHub.

```bash
git clone https://github.com/otakuc0der/airport-api.git
```

Go to the project directory.

```bash
cd airport-api
```

---

## 2. Install uv

This project uses **uv** instead of **pip** for dependency management and virtual environments.

Compared to pip, **uv** provides:

- significantly faster package installation
- reproducible dependency resolution
- built-in virtual environment management
- lock file support

Check whether `uv` is already installed.

```bash
uv --version
```

If the command is not found, install it.

### Windows

```powershell
winget install --id Astral-sh.uv
```

### Linux / macOS

Follow the official installation guide:

https://docs.astral.sh/uv/

After installation, restart your terminal and verify that `uv` is available.

```bash
uv --version
```

---

## 3. Create a Virtual Environment

The project uses **Python 3.14**.

Create a virtual environment:

```bash
uv venv --python 3.14
```

Activate it.

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
.venv\Scripts\activate.bat
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 4. Install Dependencies

Install all required packages.

```bash
uv sync
```

`uv` reads dependency versions from `uv.lock`, ensuring every developer installs exactly the same package versions.

---

# Environment Configuration

The repository contains an example environment configuration.

```text
.env.example
```

Create your local environment file.

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Current environment variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Enables debug mode |
| `FIXTURE_PASSWORD` | Password used for all generated demo users |

> **Important**
>
> The `.env` file contains local configuration and should never be committed to Git.
>
> The `.env.example` file only documents the required variables and is safe to include in the repository.

---

# Database Setup

Apply all database migrations.

```bash
uv run python manage.py migrate
```

This command creates every database table required by the project.

---

# Demo Data

The project includes a custom management command that generates realistic demonstration data.

Generate the fixture.

```bash
uv run python manage.py generate_airport_fixture
```

The generated fixture is saved to:

```text
airport/fixtures/airport_service_data_fixture.json
```

Load the fixture into the database.

```bash
uv run python manage.py loaddata airport_service_data_fixture
```

After loading the fixture, the project contains:

- Countries
- Cities
- Airports
- Airplane Types
- Airplanes
- Crew Members
- Routes
- Flights
- Orders
- Tickets
- Demo Users

The fixture is intended for local development and testing.

It provides a realistic airport booking environment without manually creating data through the Django Admin panel.

---

## Available Demo Accounts

The generated fixture includes several predefined user accounts.

The password for all accounts is the value of the `FIXTURE_PASSWORD`
environment variable (or `password123` if the variable is not specified).

| Role | Email |
|------|-------|
| Passenger | `passenger1@example.com` |
| Staff | `staff1@example.com` |
| Administrator | `admin@example.com` |

These accounts allow you to test different parts of the project immediately after loading the fixture.

To access the Django Administration panel, sign in using either the **Staff** or **Administrator** account.

---

# Creating Your Own Administrator

Loading the fixture already creates an administrator account.

Creating another administrator is completely optional.

If you prefer using your own account:

```bash
uv run python manage.py createsuperuser
```

Follow the prompts to provide your own email address and password.

---

# Running the Development Server

Start the application.

```bash
uv run python manage.py runserver
```

The project will become available at:

Application

```text
http://127.0.0.1:8000/
```

Django Administration

```text
http://127.0.0.1:8000/admin/
```

The Browsable API will become available after the REST endpoints are implemented.

# Django Administration

The project includes a customized Django Administration interface for convenient management of airport data.

The admin panel is optimized for working with interconnected models and large datasets.

Current features include:

- optimized querysets using `select_related()`
- custom list filters
- advanced search
- ordering
- calculated fields
- ticket management directly inside orders
- read-only ticket creation outside orders

The administration panel is available at:

```text
http://127.0.0.1:8000/admin/
```

Log in using one of the demo accounts or your own superuser account.

---

# Project Structure

```text
airport-api/
│
├── airport/                    # Airport application
│   ├── fixtures/
│   ├── management/
│   ├── migrations/
│   ├── admin.py
│   ├── admin_filters.py
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── filters.py
│   └── views.py
│
├── airport_service/            # Django project configuration
│
├── user/                       # Custom user application
│
├── media/
│
├── .env.example
├── pyproject.toml
├── uv.lock
├── manage.py
└── README.md
```

The project follows a modular architecture where each application has a clearly defined responsibility.

---

# Development Workflow

The project follows a Git Flow inspired workflow.

```
main
 │
 ▼
develop
 │
 ├── feature/user-model
 ├── feature/airport-models
 ├── feature/flight-models
 └── ...
```

Every feature is developed in its own branch.

Typical workflow:

```bash
git checkout develop

git pull

git checkout -b feature/new-feature
```

After completing the implementation:

```bash
git add .

git commit

git push origin feature/new-feature
```

The feature branch is merged into `develop`.

When development is finished, `develop` is merged into `main`.

---
