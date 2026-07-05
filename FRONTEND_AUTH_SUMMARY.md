# Frontend Authentication & Registration Overview

## 📁 File Structure

### Core Authentication Files
| File | Purpose |
|------|---------|
| [frontend/src/contexts/AuthContext.tsx](frontend/src/contexts/AuthContext.tsx) | Auth state management, user data, permissions |
| [frontend/src/lib/auth.ts](frontend/src/lib/auth.ts) | API calls, token storage, auth logic |
| [frontend/src/lib/auth.test.ts](frontend/src/lib/auth.test.ts) | Auth unit tests |
| [frontend/src/pages/Login.tsx](frontend/src/pages/Login.tsx) | Login landing page with Telegram widget + email/password form |
| [frontend/src/pages/Register.tsx](frontend/src/pages/Register.tsx) | KYC registration form |
| [frontend/src/pages/AuthCallback.tsx](frontend/src/pages/AuthCallback.tsx) | Auth redirect handler (redirects to `/login`) |
| [frontend/src/pages/AuthError.tsx](frontend/src/pages/AuthError.tsx) | Auth error page with countdown redirect |
| [frontend/src/components/TelegramLoginWidget.tsx](frontend/src/components/TelegramLoginWidget.tsx) | Telegram OAuth widget wrapper |
| [frontend/src/components/PinAuthDialog.tsx](frontend/src/components/PinAuthDialog.tsx) | 6-digit PIN authentication dialog |

---

## 🔐 Current Authentication Mechanisms

### 1. **Telegram Login (Primary)**
- **Location:** [Login.tsx](frontend/src/pages/Login.tsx) + [TelegramLoginWidget.tsx](frontend/src/components/TelegramLoginWidget.tsx)
- **Flow:**
  1. User clicks official Telegram login button
  2. Telegram widget shows popup with OAuth
  3. `onTelegramAuth()` callback fires with user data (id, hash, auth_date, username, photo_url)
  4. Data sent to `/api/v1/auth/telegram-login-widget` endpoint
  5. Backend validates hash signature and returns JWT token
  6. Token stored in `localStorage` as `token`
  7. User redirected to dashboard

- **Key Features:**
  - Bot username dynamically fetched from `/api/v1/auth/telegram-login-config` 
  - Cloudflare Turnstile CAPTCHA support (optional) — required when `VITE_TURNSTILE_SITE_KEY` set
  - Turnstile token passed to backend if available
  - No password required

### 2. **Email/Password Login (Secondary)**
- **Location:** [Login.tsx](frontend/src/pages/Login.tsx)
- **Flow:**
  1. Form collects email + password
  2. Sent to `/api/v1/auth/terminal-login` endpoint
  3. Backend returns JWT token
  4. Token stored in `localStorage`
  5. User authenticated

- **Key Features:**
  - Optional Turnstile verification before submit
  - Simple validation (email + password required)
  - Less documented than Telegram flow

### 3. **PIN Authentication (Secondary)**
- **Location:** [PinAuthDialog.tsx](frontend/src/components/PinAuthDialog.tsx)
- **Purpose:** 6-digit PIN verification for sensitive operations
- **UI:** Dialog with OTP input grid + authorize/cancel buttons
- **Usage:** Likely used for transaction approvals or sensitive settings changes

---

## 📋 Registration Flow (KYC)

### Current Registration Page ([Register.tsx](frontend/src/pages/Register.tsx))
- **Type:** KYC/KYB application form (not traditional sign-up)
- **Purpose:** Request access to admin dashboard
- **Required Fields:**
  - Full Name
  - Email
  - Phone Number
  - Telegram Username ⭐ (required for approval notifications)
  - Business Name (optional)
  - Address (optional)

- **Form Validation:**
  - Manual validation (no Zod schema)
  - Checks: full_name, email, phone, telegram_username are not empty
  - Email format NOT validated
  - Basic string trimming

- **Submission:**
  - POST to `/api/v1/auth/register`
  - Returns KYB ID + Xendit customer ID
  - Success page shows application ID and status
  - Users notified via Telegram after admin approval

- **UX Features:**
  - Left panel with 4-step process guide (desktop only)
  - Social platform links (Telegram, WhatsApp, Messenger)
  - Branded styling with emerald green theme
  - Success confirmation with application tracking info

---

## 🎣 Validation & Schemas

### Zod Schemas Found:
**Only 1 validation schema exists in the frontend:**
- [POSTerminal.tsx](frontend/src/components/POSTerminal.tsx) — Transaction form schema:
  ```typescript
  const transactionSchema = z.object({
    description: z.string().min(1, 'Description required'),
    amount: z.number().positive('Amount must be positive'),
    payment_method: z.enum(['maya', 'card', 'gcash', 'grabpay']),
    customer_name: z.string().optional(),
    customer_email: z.string().email().optional().or(z.literal('')),
    customer_phone: z.string().optional(),
  });
  ```

### Auth Schemas:
- **No Zod schemas in auth flows**
- Manual validation in:
  - [AuthContext.tsx](frontend/src/contexts/AuthContext.tsx) — generic error handling
  - [Login.tsx](frontend/src/pages/Login.tsx) — basic field checks
  - [Register.tsx](frontend/src/pages/Register.tsx) — basic field checks
  - [Merchants.tsx](frontend/src/pages/Merchants.tsx) — manual email regex validation

---

## 🔑 Token Management

### Storage
- **Key:** `token` (in `localStorage`)
- **Type:** JWT bearer token
- **Retrieved in:** [auth.ts](frontend/src/lib/auth.ts) via `getStoredToken()`

### HTTP Headers
- **Auto-injected** via [api.ts](frontend/src/lib/api.ts):
  ```typescript
  headers.set('Authorization', `Bearer ${token}`);
  ```
- Applied to **all API requests** (window.fetch interceptor)

### Clearing
- `logout()` calls `clearStoredToken()` and deletes localStorage entry

---

## 👤 User & Permissions Model

### User Interface ([AuthContext.tsx](frontend/src/contexts/AuthContext.tsx))
```typescript
interface User {
  id: string;
  email: string;
  name?: string;
  role: string;
  organization_id?: string;
  organization_name?: string;
  permissions?: UserPermissions;
}

interface UserPermissions {
  is_super_admin: boolean;
  can_manage_payments: boolean;
  can_manage_disbursements: boolean;
  can_view_reports: boolean;
  can_manage_wallet: boolean;
  can_manage_transactions: boolean;
  can_manage_bot: boolean;
  can_approve_topups: boolean;
  can_manage_team: boolean;
}
```

### API Endpoint
- GET `/api/v1/auth/me` — returns current user + permissions
- Called on app load via `checkAuthStatus()` in AuthProvider

### Role-Based Access
- Components: [ProtectedAdminRoute.tsx](frontend/src/components/ProtectedAdminRoute.tsx), [RequireSuperAdmin.tsx](frontend/src/components/RequireSuperAdmin.tsx), [RequireDeveloperRole.tsx](frontend/src/components/RequireDeveloperRole.tsx)
- Checks: `user?.role === 'admin'`, `permissions?.is_super_admin`, etc.

---

## 🪝 Auth Context & Hooks

### Available Methods ([AuthContext.tsx](frontend/src/contexts/AuthContext.tsx))
```typescript
const { 
  user,              // Current user or null
  loading,           // Auth status loading
  error,             // Error message
  login,             // Email/password login
  loginWithTelegram, // Telegram OAuth login
  logout,            // Logout & clear token
  refetch,           // Re-fetch current user
  isAdmin,           // Helper: user.role === 'admin'
  isSuperAdmin,      // Helper: permissions.is_super_admin
  permissions        // Full permissions object
} = useAuth();
```

### Auto-Redirect
- If already logged in: Login page redirects to `/intro`
- If not authenticated: Protected routes should use guards

---

## 📱 API Integration Points

### Auth Endpoints Called from Frontend
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/me` | GET | Get current user + permissions |
| `/api/v1/auth/telegram-login-widget` | POST | Telegram OAuth login |
| `/api/v1/auth/terminal-login` | POST | Email/password login |
| `/api/v1/auth/register` | POST | Submit KYC registration |
| `/api/v1/auth/social-config` | GET | Get Telegram/WhatsApp/Messenger handles |
| `/api/v1/auth/telegram-login-config` | GET | Get bot username |

---

## ✅ Areas for Improvement

### 1. **Validation Schemas**
- **Current State:** No Zod/form validation in auth flows
- **Recommendation:** Add Zod schemas for:
  - Login form (email format, password length)
  - Registration form (phone pattern, email format, telegram handle pattern)
  - Use `react-hook-form` + `zod` like POSTerminal does

### 2. **Error Handling**
- **Current:** Generic error messages from backend
- **Recommendation:**
  - Specific error codes (e.g., "USER_NOT_FOUND", "INVALID_TOKEN")
  - User-friendly messages with troubleshooting hints
  - Retry logic for network failures

### 3. **Registration Form**
- **Current:** Basic form, no real-time validation
- **Recommendation:**
  - Add Telegram username format validation (must start with `@`)
  - Email format validation
  - Phone number validation (support Philippine formats)
  - Show character counts/limits
  - Add terms & privacy policy checkboxes

### 4. **Session Management**
- **Current:** Token stored in localStorage (vulnerable to XSS)
- **Recommendation:**
  - Consider httpOnly cookies with CSRF protection
  - Token refresh mechanism (if backend supports)
  - Session timeout warnings

### 5. **Telegram Widget**
- **Current:** Dynamically loaded, recreated on mount
- **Recommendation:**
  - Cache bot username to avoid repeated fetches
  - Error boundary if Telegram CDN fails
  - Fallback to email login if widget unavailable

### 6. **PIN Dialog**
- **Current:** Component exists but not integrated in visible flows
- **Recommendation:**
  - Document where PIN is used
  - Add attempt limiting to prevent brute force
  - Show time-based PIN expiry

### 7. **Testing**
- **Current:** Only `auth.test.ts` with basic tests
- **Recommendation:**
  - Test auth context with different user roles
  - Test protected routes
  - Test token refresh flow
  - Integration tests for full login flow

### 8. **Social Config**
- **Current:** Fetches from `/api/v1/auth/social-config` but only WhatsApp/Messenger used
- **Recommendation:**
  - Document which social platforms are actually integrated
  - Add links with proper UTM parameters for tracking

---

## 🔄 User Journey Map

```
┌─────────────────┐
│  Landing Page   │ (Login.tsx)
│  (Hero Section) │
└────────┬────────┘
         │
    ┌────▼─────────────────────────────┐
    │ User not authenticated?           │
    └────┬─────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────────┐
    │ Choose auth method:                             │
    │ 1. Telegram OAuth (recommended)                 │
    │ 2. Email/Password                               │
    │ 3. Register for KYC access                      │
    └────┬─────────┬──────────────┬───────────────────┘
         │         │              │
    ┌────▼─┐  ┌────▼──┐  ┌────────▼──────────┐
    │ TG   │  │Email  │  │ Register / KYC    │
    │OAuth │  │Login  │  │ Form              │
    └────┬─┘  └────┬──┘  └────────┬──────────┘
         │         │              │
    ┌────▼─────────▼──┐   ┌───────▼──────────┐
    │ Get JWT Token   │   │ Submit to        │
    │ Store in LS     │   │ /api/auth/reg    │
    └────┬────────────┘   └───────┬──────────┘
         │                        │
    ┌────▼────────────────┐   ┌───▼──────────────┐
    │ Fetch /api/auth/me  │   │ Wait for admin   │
    │ Load permissions    │   │ approval via TG  │
    └────┬────────────────┘   └───┬──────────────┘
         │                        │
    ┌────▼──────────┐        ┌────▼──────────────┐
    │ → /intro      │        │ Approved? Retry   │
    │ → Dashboard   │        │ login with TG     │
    └───────────────┘        └───────────────────┘
```

---

## 📊 Component Dependency Graph

```
AuthContext.tsx
├── useAuth() hook
│   ├── Login.tsx
│   ├── AuthCallback.tsx
│   ├── Protected routes
│   └── Dashboard pages
├── authApi methods
│   └── lib/auth.ts
│       ├── API calls
│       ├── Token management
│       └── localStorage
└── LanguageContext.tsx (sibling)
```

---

## 🚀 Quick Reference

### To Add New Auth Method:
1. Add API endpoint in [auth.ts](frontend/src/lib/auth.ts)
2. Add method to `authApi` object
3. Add context method in [AuthContext.tsx](frontend/src/contexts/AuthContext.tsx)
4. Call from login page or create new login variant

### To Protect a Route:
```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyPage() {
  const { user, loading } = useAuth();
  
  if (loading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" />;
  
  return <div>Protected content</div>;
}
```

### To Check Permissions:
```typescript
const { permissions } = useAuth();

if (!permissions?.can_manage_payments) {
  return <Forbidden />;
}
```

---

**Last Updated:** 2026-07-03  
**Project:** xend (paybot)  
**Frontend Stack:** React 18 + TypeScript + TailwindCSS
