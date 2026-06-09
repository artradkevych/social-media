# Social Media API

A RESTful API for a social media platform built with Django and Django REST Framework.

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

## Run with Docker

Build image:

```bash
docker build -t social-media-api .
```

Run container:

```bash
docker run -p 8000:8000 social-media-api
```

## Authentication

The API uses **token-based authentication**.

1. Register at `POST /api/users/register/`
2. Login at `POST /api/users/login/` — you will receive a token
3. Pass the token in the `Authorization` header for all protected endpoints:

```
Authorization: Token <your-token>
```

## API Documentation

| UI | URL |
|----|-----|
| Swagger UI | http://127.0.0.1:8000/api/doc/swagger/ |
| Redoc | http://127.0.0.1:8000/api/doc/redoc/ |
