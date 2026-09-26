# TenantMLE

TenantMLE is a multi-tenant learning platform with a Django REST API, PostgreSQL database, JWT authentication, and a React/Vite frontend.

## Requirements

- Python 3.13+
- Node.js and npm
- Docker Desktop with Docker Compose

## Setup

### 1. Configure the environment

Copy the example environment file to `.env` in the project root:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `SECRET_KEY` with a local development secret.

### 2. Set up the backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Generate a unique Django secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated value into `.env` as the value of `SECRET_KEY`.

### 3. Start PostgreSQL

```powershell
docker compose up -d postgres
```

### 4. Prepare the database

From the project root, with the virtual environment activated:

```powershell
Set-Location src
python manage.py migrate
python manage.py createsuperuser
```

## Run the application

### Start the backend

From `src`:

```powershell
python manage.py runserver 8000
```

The API is available at <http://localhost:8000/api/>.

### Start the frontend

Open a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open <http://localhost:5173/>.

The frontend automatically proxies API requests to the backend at `http://localhost:8000`.

## Run tests

With PostgreSQL running, from `src`:

```powershell
python manage.py test
```

To build the frontend:

```powershell
Set-Location ..\frontend
npm run build
```

## Stop PostgreSQL

```powershell
docker compose stop postgres
```
