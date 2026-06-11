# Social Media API

A RESTful API for a social media platform built with Django and Django REST Framework.

## Getting Started

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <project-folder>
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
SECRET_KEY=your-secret-key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=social-media
POSTGRES_HOST=localhost
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start server:
```bash
python manage.py runserver
```

## Docker Compose

1. Create `.env` file:
```env
POSTGRES_PASSWORD=social-media
POSTGRES_USER=social-media
POSTGRES_DB=social-media
POSTGRES_HOST=db
PGDATA=/var/lib/postgresql/data
SECRET_KEY=your-secret-key
```

2. Start application:
```bash
docker compose up --build
```

3. Stop application:
```bash
docker compose down
```

## Authentication

The API uses token-based authentication. Pass the token in the `Authorization` header:

```
Authorization: Token <your-token>
```

1. Register: `POST /api/users/register/`
2. Login: `POST /api/users/login/` — receive token
3. Use token for protected endpoints

## Documentation

- Swagger UI: http://localhost:8000/api/doc/swagger/
- ReDoc: http://localhost:8000/api/doc/redoc/