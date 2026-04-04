# Authentication System - Knowledge OS

This document describes the JWT-based authentication system implemented for Knowledge OS.

## Overview

The authentication system provides:
- User registration with email/username
- JWT-based authentication (access + refresh tokens)
- Password hashing with bcrypt
- Password reset flow
- Protected routes/endpoints
- Session persistence across page reloads

## Backend (FastAPI)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | Auto-generated (dev only) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry time | `1440` (24 hours) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry time | `7` (days) |
| `RESET_TOKEN_EXPIRE_HOURS` | Password reset token expiry | `1` (hour) |

**Important**: Set `JWT_SECRET_KEY` in production! A random key is generated for development only.

### API Endpoints

All endpoints are prefixed with `/api/auth`.

#### POST `/api/auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "display_name": "John Doe",  // optional
  "password": "securepassword123"
}
```

**Response:** `TokenResponse`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "display_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST `/api/auth/login`
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `TokenResponse` (same as register)

#### POST `/api/auth/refresh`
Refresh an access token using a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `TokenResponse` (same as register)

#### POST `/api/auth/logout`
Logout by invalidating the refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

#### GET `/api/auth/me`
Get the current authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `UserResponse`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "display_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST `/api/auth/password-reset`
Request a password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account with this email exists, a password reset token has been sent",
  "_dev_token": "uuid"  // Only in development
}
```

#### POST `/api/auth/password-reset/confirm`
Confirm a password reset with the token.

**Request:**
```json
{
  "token": "reset-token-uuid",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "message": "Password has been reset successfully"
}
```

### Protected Routes

To protect a route, use the `get_current_user` dependency:

```python
from app.middleware.auth import get_current_user
from fastapi import Depends

@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}"}
```

### Database Tables

#### `users`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `email` | TEXT | Unique, indexed |
| `username` | TEXT | Unique, indexed |
| `display_name` | TEXT | Optional display name |
| `hashed_password` | TEXT | Bcrypt hash |
| `is_active` | INTEGER | Active status (0/1) |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update |

#### `refresh_tokens`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `user_id` | TEXT | Foreign key → users |
| `token_hash` | TEXT | Hashed refresh token |
| `expires_at` | TIMESTAMP | Expiration time |
| `created_at` | TIMESTAMP | Creation time |

#### `password_reset_tokens`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `user_id` | TEXT | Foreign key → users |
| `token_hash` | TEXT | Hashed reset token |
| `expires_at` | TIMESTAMP | Expiration time |
| `used` | INTEGER | Token used status (0/1) |
| `created_at` | TIMESTAMP | Creation time |

## Frontend (React + TypeScript)

### Auth Store (Zustand)

The `useAuthStore` provides authentication state and actions:

```typescript
import { useAuthStore } from '@/stores/auth'

const {
  user,
  isAuthenticated,
  isLoading,
  error,
  login,
  register,
  logout,
  refreshUser,
  clearError
} = useAuthStore()
```

**State:**
- `user: User | null` - Current user object
- `isAuthenticated: boolean` - Auth status
- `isLoading: boolean` - Loading state
- `error: string | null` - Error message

**Actions:**
- `login(email, password)` - Login user
- `register(data)` - Register new user
- `logout()` - Logout and clear tokens
- `refreshUser()` - Fetch current user from API
- `clearError()` - Clear error message

### API Client

The auth API is available via `authApi`:

```typescript
import { authApi } from '@/services/api'

// Login
const response = await authApi.login(email, password)

// Register
const response = await authApi.register({
  email,
  username,
  password,
  display_name
})

// Logout
await authApi.logout(refreshToken)

// Get current user
const user = await authApi.getMe()

// Password reset
await authApi.requestPasswordReset(email)
await authApi.confirmPasswordReset(token, newPassword)
```

### Protected Routes

Use the `<ProtectedRoute>` component to protect routes:

```tsx
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

<Route
  path="/protected"
  element={
    <ProtectedRoute>
      <MyProtectedPage />
    </ProtectedRoute>
  }
/>
```

### Token Management

Tokens are automatically:
- Stored in `localStorage` (`access_token`, `refresh_token`)
- Attached to API requests via axios interceptor
- Refreshed automatically on 401 responses
- Cleared on logout

## Security Considerations

1. **JWT Secret**: Always set `JWT_SECRET_KEY` in production
2. **HTTPS**: Use HTTPS in production to protect tokens in transit
3. **Token Expiry**: Configure appropriate expiry times for your use case
4. **Password Requirements**: Minimum 8 characters (enforced on frontend)
5. **Password Reset**: Tokens expire after 1 hour by default
6. **Refresh Tokens**: Stored hashed in database, can be revoked

## Development Setup

1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. The SQLite database tables will be created automatically on first run.

3. Start the backend server:
```bash
uvicorn app.main:app --reload
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Start the frontend dev server:
```bash
npm run dev
```

6. Navigate to `http://localhost:5173/login` to register/login.

## Testing

In development, the password reset token is returned in the API response (`_dev_token` field) and logged to the console. In production, you would implement email sending.

## Files Created/Modified

### Backend:
- `backend/app/models/user.py` - User Pydantic models
- `backend/app/services/auth.py` - AuthService (JWT, password hashing)
- `backend/app/routers/auth.py` - Auth API endpoints
- `backend/app/middleware/auth.py` - get_current_user dependency
- `backend/app/config.py` - JWT settings
- `backend/app/database/sqlite.py` - Auth tables
- `backend/requirements.txt` - JWT dependencies
- `backend/app/main.py` - Register auth router

### Frontend:
- `frontend/src/services/api.ts` - Auth API functions & interceptors
- `frontend/src/stores/auth.ts` - Auth Zustand store
- `frontend/src/pages/LoginPage.tsx` - Login/Register page
- `frontend/src/pages/ResetPasswordPage.tsx` - Password reset page
- `frontend/src/components/auth/ProtectedRoute.tsx` - Route protection
- `frontend/src/components/ui/card.tsx` - Card UI component
- `frontend/src/App.tsx` - Auth routes
- `frontend/src/components/layout/Sidebar.tsx` - User info & logout
