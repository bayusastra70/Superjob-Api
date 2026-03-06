Python | FastAPI | PostgreSQL | WebSocket 

# 🚀 SuperJob API

**SuperJob API** is a backend service for a **job recruitment platform** where candidates can apply for jobs and recruiters can manage hiring processes efficiently.

The API is built using **FastAPI** with a modular and scalable architecture. It includes features such as **job management, application tracking, recruiter tools, and real-time communication using WebSockets**.

---

# ✨ Features

### 👤 Authentication & User Management

* User registration and login
* JWT-based authentication
* Role-based access control
* User profile management

### 💼 Job Management

* Create and manage job postings
* Search and filter job listings
* Job detail endpoints

### 📄 Application Tracking System (ATS)

* Candidates can apply for jobs
* Recruiters can review applications
* Track application status
* Manage rejection reasons

### 🏢 Company Management

* Company profile management
* Recruiter team member management
* Role-based recruiter access

### 💬 Real-time Chat

* Messaging between recruiters and candidates
* WebSocket-based real-time communication

### 📅 Interview System

* Schedule interviews
* Provide interview feedback

### 🔔 Notification System

* Activity tracking
* Real-time notifications

### 📄 CV Processing

* Upload candidate CV
* Basic CV information extraction

---

# 🏗 Architecture

This project uses a **layered architecture** to keep the codebase clean, maintainable, and scalable.

```
app
 ├ api
 │   ├ routers        # API endpoints
 │   ├ ws             # WebSocket endpoints
 │   └ deps.py        # Dependencies
 │
 ├ core               # Security & configuration
 ├ db                 # Database connection
 ├ models             # SQLAlchemy models
 ├ schemas            # Pydantic schemas
 ├ services           # Business logic
 ├ utils              # Helper utilities
 └ cron               # Scheduled jobs
```

Architecture flow:

```
Client
   │
   ▼
FastAPI Router
   │
   ▼
Service Layer
   │
   ▼
Database (PostgreSQL)
```

---

# 🛠 Tech Stack

* **Python**
* **FastAPI**
* **PostgreSQL**
* **SQLAlchemy**
* **Alembic (Database Migration)**
* **Pydantic**
* **WebSocket**
* **Pytest**
* **Docker (optional)**

---

# ⚙️ Installation Guide

## 1. Clone the Repository

```
git clone https://github.com/bayusastra70/Superjob-Api.git
cd Superjob-Api
```

---

## 2. Create Virtual Environment

### Windows

```
python -m venv .venv
.venv\Scripts\activate
```

### Linux / MacOS

```
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## 4. Run Database Migration

```
alembic upgrade head
```

---

## 5. Seed Dummy User Data

```
python -m app.db.seeds.user_seed
```

---

## 6. Run the Development Server

```
uvicorn app.main:app --reload
```

The server will run at:

```
http://localhost:8000
```

---

# 📘 API Documentation

FastAPI automatically generates interactive API documentation.

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# 🧪 Running Tests

```
pytest
```

---

# 🐳 Docker (Optional)

Build the Docker image:

```
docker build -t superjob-api .
```

Run the container:

```
docker run -p 8000:8000 superjob-api
```

---

# 📌 Example API Endpoints

Authentication

```
POST /auth/login
POST /auth/register
```

Jobs

```
GET /jobs
POST /jobs
GET /jobs/{id}
```

Applications

```
POST /applications
GET /applications
```

Chat (WebSocket)

```
WS /chat/ws
```

---

# 📈 Future Improvements

* AI-powered job recommendation
* Advanced job search filters
* Improved resume skill extraction
* Mobile optimized API

---

# 👨‍💻 Author

Developed as part of an **internship backend project**.

This repository is shared for **portfolio and learning purposes**.
