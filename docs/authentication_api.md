# Authentication API Documentation

> **Last Updated:** 2025-12-22

## Overview

SuperJob API memiliki sistem autentikasi terpisah untuk dua jenis pengguna:

1. **Corporate** - Employer, Recruiter, Admin
2. **Talent** - Job Seeker, Candidate

---

## Authentication Endpoints

### Corporate (Employer/Admin)

| Method | Endpoint                   | Description                    |
| ------ | -------------------------- | ------------------------------ |
| POST   | `/auth/corporate/login`    | Login untuk Corporate          |
| POST   | `/auth/corporate/register` | Registrasi akun Corporate baru |

### Talent (Candidate)

| Method | Endpoint                | Description                        |
| ------ | ----------------------- | ---------------------------------- |
| POST   | `/auth/talent/login`    | Login untuk Talent                 |
| POST   | `/auth/talent/register` | Registrasi akun Talent baru        |
| POST   | `/auth/talent/google`   | Login/Register dengan Google OAuth |

### Password Reset

| Method | Endpoint                | Description                 |
| ------ | ----------------------- | --------------------------- |
| POST   | `/auth/forgot-password` | Request reset password      |
| POST   | `/auth/reset-password`  | Reset password dengan token |

### Token Refresh

| Method | Endpoint        | Description                              |
| ------ | --------------- | ---------------------------------------- |
| POST   | `/auth/refresh` | Get new access token using refresh token |

### Common

| Method | Endpoint      | Description                          |
| ------ | ------------- | ------------------------------------ |
| GET    | `/auth/me`    | Get current user info                |
| POST   | `/auth/token` | [LEGACY] Login dengan email/password |

---

## Token System

SuperJob menggunakan sistem dual-token untuk keamanan:

| Token Type        | Expiry   | Purpose                             |
| ----------------- | -------- | ----------------------------------- |
| **Access Token**  | 30 menit | Untuk akses API (Bearer token)      |
| **Refresh Token** | 7 hari   | Untuk mendapatkan access token baru |

---

## Corporate Authentication

### 1. Corporate Login

**Endpoint:** `POST /auth/corporate/login`

**Request Body:**

```json
{
  "email": "employer@superjob.com",
  "password": "employer123"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_expires_in": 604800,
  "user": {
    "id": 8,
    "email": "employer@superjob.com",
    "full_name": "Employer 1",
    "role": "employer",
    "is_superuser": false
  }
}
```

**Test Credentials:**
| Email | Password | Role |
|-------|----------|------|
| `employer@superjob.com` | `employer123` | employer |
| `tanaka@gmail.com` | `password123` | employer |
| `admin@superjob.com` | `admin123` | admin |

---

### 2. Corporate Registration

**Endpoint:** `POST /auth/corporate/register`

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contact_name` | string | ✓ | Nama contact person |
| `company_name` | string | ✓ | Nama perusahaan |
| `email` | string | ✓ | Email bisnis |
| `phone_number` | string | ✓ | Nomor telepon (+62...) |
| `password` | string | ✓ | Password (min 8 karakter) |
| `nib_document` | file | ✗ | NIB Document (PDF, max 5MB) |

**Response (201 Created):**

```json
{
  "message": "Registrasi berhasil. Silakan tunggu verifikasi akun.",
  "user_id": 100,
  "email": "hr@teknologimaju.com",
  "company_name": "PT Teknologi Maju",
  "role": "employer",
  "is_verified": false
}
```

---

## Talent Authentication

### 1. Talent Login

**Endpoint:** `POST /auth/talent/login`

**Request Body:**

```json
{
  "email": "candidate@superjob.com",
  "password": "candidate123"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 9,
    "email": "candidate@superjob.com",
    "full_name": "Candidate 1",
    "role": "candidate"
  }
}
```

**Test Credentials:**
| Email | Password |
|-------|----------|
| `candidate@superjob.com` | `candidate123` |
| `john.doe@example.com` | `password123` |

---

### 2. Talent Registration

**Endpoint:** `POST /auth/talent/register`

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Nama lengkap |
| `email` | string | ✓ | Email |
| `password` | string | ✓ | Password (min 8 karakter) |
| `cv_file` | file | ✗ | CV (PDF, max 10MB) |

**Response (201 Created):**

```json
{
  "message": "Registrasi berhasil. Selamat datang di SuperJob!",
  "user_id": 101,
  "email": "jane.smith@gmail.com",
  "name": "Jane Smith",
  "role": "candidate"
}
```

---

### 3. Google OAuth (Talent Only)

**Endpoint:** `POST /auth/talent/google`

> ⚠️ **Status:** Not yet implemented

**Request Body:**

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Expected Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 101,
    "email": "jane.smith@gmail.com",
    "name": "Jane Smith",
    "role": "candidate"
  },
  "is_new_user": false
}
```

---

## Password Reset

### 1. Forgot Password

**Endpoint:** `POST /auth/forgot-password`

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**

```json
{
  "message": "Jika email terdaftar, link reset password telah dikirim."
}
```

> **Note:** Response selalu sama untuk keamanan (tidak mengungkapkan apakah email terdaftar atau tidak)

---

### 2. Reset Password

**Endpoint:** `POST /auth/reset-password`

> ⚠️ **Status:** Not yet implemented

**Request Body:**

```json
{
  "token": "abc123...",
  "new_password": "NewSecurePassword123"
}
```

---

## Refresh Token

### Refresh Access Token

**Endpoint:** `POST /auth/refresh`

Gunakan refresh token untuk mendapatkan access token baru tanpa login ulang.

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": null,
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Flow:**

```
1. Login → Mendapat access_token + refresh_token
2. Gunakan access_token untuk API requests
3. Ketika access_token expired (401 error)
4. Kirim refresh_token ke /auth/refresh
5. Mendapat access_token baru
6. Lanjutkan API requests dengan access_token baru
7. Jika refresh_token expired → User harus login ulang
```

**Error Responses:**

| Status | Description                        |
| ------ | ---------------------------------- |
| 401    | Refresh token invalid atau expired |

---

## Role-Based Access Control

| Role        | Description            | Login Endpoint          |
| ----------- | ---------------------- | ----------------------- |
| `admin`     | System administrator   | `/auth/corporate/login` |
| `employer`  | Company HR / Recruiter | `/auth/corporate/login` |
| `candidate` | Job seeker             | `/auth/talent/login`    |

**Important:**

- Corporate login endpoint (`/auth/corporate/login`) only accepts users with role `employer` or `admin`
- Talent login endpoint (`/auth/talent/login`) only accepts users with role `candidate`
- Attempting to login with wrong role will return `403 Forbidden`

---

## Error Responses

| Status Code | Description                              |
| ----------- | ---------------------------------------- |
| 400         | Bad Request - Invalid input data         |
| 401         | Unauthorized - Invalid credentials       |
| 403         | Forbidden - Wrong user type for endpoint |
| 422         | Validation Error - Invalid field format  |
| 500         | Internal Server Error                    |

**Example Error Response:**

```json
{
  "detail": "Email atau password salah"
}
```

---

## Using the Access Token

After successful login, include the token in subsequent requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Swagger UI:**

1. Click the **Authorize** button (🔒)
2. Enter: `Bearer <your_token>`
3. Click **Authorize**

---

## Design Reference

| Screen  | Endpoint                   | Description                                     |
| ------- | -------------------------- | ----------------------------------------------- |
| Image 1 | `/auth/corporate/login`    | "Welcome, Partner!" - Corporate login           |
| Image 2 | `/auth/corporate/register` | "Welcome to Superjob" - Corporate register      |
| Image 3 | `/auth/talent/login`       | "Welcome Back!" - Talent login with Google      |
| Image 4 | `/auth/talent/register`    | "Welcome to SuperJob" - Talent register with CV |
