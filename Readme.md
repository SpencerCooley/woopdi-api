# Woopdi API - Multi-tenant SaaS Platform

## Overview
This repository contains a backend for a multi-tenant SaaS platform built with FastAPI, Celery, Redis, and PostgreSQL. Everything is containerized and can be run locally for development.

## System Design
The application follows a distributed architecture pattern with the following key components:

![System Architecture Diagram](/api/static/system-architecture1.png)

### Components
- **FastAPI Backend**: Handles HTTP requests and serves as the main API gateway
- **Celery Workers**: Process asynchronous tasks and long-running operations
- **Redis**: Serves dual purposes:
  - Message broker for Celery task queue
  - Caching layer for temporary data storage
- **PostgreSQL**: Persistent storage for application data

### Data Flow
1. Clients send requests to the FastAPI backend
2. For long-running operations, the backend dispatches tasks to Celery workers via Redis
3. Celery workers process tasks asynchronously and publish results to Redis
4. Websocket endpoints are used to stream results to the client by subscribing to Redis channels
5. Permanent data is stored in PostgreSQL

## Prerequisites
- Docker and Docker Compose installed on your system

## Setup Process (Development)

### 1. Clone Repository
```bash
git clone <repository-url>
cd woopdi-api
```

### 2. Environment Configuration
Create a `.env` file in the root directory (same level as `docker-compose.yml`) with the following variables based on `.env.example`:

```env
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# PostgreSQL Configuration
POSTGRES_USER=development
POSTGRES_PASSWORD=devpass
POSTGRES_DB=name_your_database
POSTGRES_PORT=5432

# Google Cloud Storage (Optional)
GCP_BUCKET_NAME=your-gcp-bucket-name
GCP_SERVICE_FILE_CRED_JSON_LOCATION=your-json-service-file

# Email Configuration (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_sendgrid_from_email

# Stripe Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Celery Configuration
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# URL Configuration
API_HOST=127.0.0.1
WEB_CLIENT_URL=http://localhost:3000

# Security Keys
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# Environment
IS_PROD=False

# AI Services (Optional)
REPLICATE_API_TOKEN=your-replicate-api-token
```

**Google Cloud Storage (Optional)**:
If you want to use Google Cloud Storage features, get your service key from Google Cloud Console and include its location in the `.env`.

The `.env` file is gitignored so it won't be committed to the repository.

### 3. Start the Application
```bash
docker compose up
```

This command will build all containers and start them, including:
- FastAPI application
- Celery workers
- Redis
- PostgreSQL

### 4. Seed the Database
Open another terminal and run the seed to have test users and organizations:

```bash
docker exec -it woopdi_fastapi_app /bin/bash
python seed/seed_database.py
```

The seed creates:
- System users (superadmin, admin)
- Organization users with test organizations
- Various roles (ADMIN, MODERATOR, MEMBER)
- Test data for development and testing

### 5. Access the Application
- **API**: http://localhost:8000
- **API OAS Documentation**: http://localhost:8000/docs
- **API OAS Documentation Redoc**: http://localhost:8000/redoc
- **Interactive Terminal**: `docker exec -it woopdi_fastapi_app /bin/bash`

## Testing

### Running Tests
```bash
# Run all tests
docker exec woopdi_fastapi_app pytest

# Interactive testing
docker exec -it woopdi_fastapi_app /bin/bash
```

### Test Structure
Tests mirror the development seed structure for consistency. The test configuration in `tests/conftest.py` creates the same users and organizations as the development seed.

## Database Migrations

### System Architecture
The system uses SQLAlchemy as an ORM and Alembic for migrations.

### Generating Migrations
When you make changes to models:

1. Get into the container:
```bash
docker exec -it woopdi_fastapi_app /bin/bash
```

2. Generate migration:
```bash
alembic revision --autogenerate -m "added a new field to the project model"
```

3. Fix permissions (important!):
```bash
chmod 777 alembic/versions/your-new-migration-file.py
```

### Running Migrations
Migrations are run automatically when you start the containers. If you need to run them manually:

```bash
alembic upgrade head
```

## Docker Management

### Common Commands
```bash
# Stop containers
docker compose down --remove-orphans

# Clear all volume data (fresh start)
docker compose down --remove-orphans -v

# Restart after stopping
docker compose down --remove-orphans
docker compose up

# View logs
docker compose logs -f

# View container status
docker compose ps
```

## Seeding Strategy

### Development Seeding
```bash
docker exec -it woopdi_fastapi_app /bin/bash
python seed/seed_database.py
```

### Adding New Models to Seed
When adding new models that need seed data, use AI to help update the seed files. The AI is usually very good at understanding the existing pattern and adding appropriate test data.

## Organization and User Structure

### User Types
- **System Level Users** (not associated with organizations):
  - `superadmin` - Full system access
  - `admin` - Limited system access

- **Organization Level Users**:
  - `ADMIN owner` - Admin of organization AND owner of non-solo organization
  - `ADMIN` - Admin of organization but not necessarily the owner
  - `MODERATOR` - Middle tier for privileges
  - `MEMBER` - Regular organization user

look at the acutal seed files to understand the different user types in the system.

### Middleware
The API uses middleware functions to gate endpoints. This approach is simple and easily modifiable - just add new functions or modify existing ones as needed.

### Solo vs Non-Solo Organizations

**Solo Organizations**:
- Automatically assigned to all users who enter the system (signup or invite)
- Provide personal workspace/context for each user
- All users are ADMIN owners of their solo organization
- Used for inviting people to collaborate

**Non-Solo Organizations**:
- Created when users need their own organization space
- Users can only own 1 non-solo organization in this starter template
- Endpoint: `POST /organizations/create-organization`
- For users who were invited but need their own organization

### Known Issues & Solutions

**Issue**: Invited users don't get a solo organization automatically
**Solution**: Use `POST /organizations/create-organization` endpoint to create a non-solo organization for users who don't have one yet.

## Production Setup


### Deployment Notes
Production setup is similar to development since everything is containerized. Consider using managed services for:
- PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- Redis (AWS ElastiCache, Google Memorystore, etc.)
- File storage GCP production bucket


This setup provides a clean, consistent development environment that mirrors production architecture.
