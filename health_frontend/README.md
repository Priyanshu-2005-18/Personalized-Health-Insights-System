# VitalIQ — Personalized Health Insights Frontend

A production-ready React + TypeScript frontend for the Personalized Health Insights System.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Styling | Tailwind CSS 3 |
| Routing | React Router v6 |
| HTTP | Axios (with auto token refresh) |
| State | Zustand (persisted auth + health store) |
| Charts | Recharts |
| Icons | Lucide React |
| Container | Docker + nginx |

---

## Project Structure

```
src/
├── api/
│   ├── client.ts          # Axios instance — Bearer token + 401 auto-refresh
│   ├── auth.ts            # login, register, logout, getMe
│   ├── health.ts          # health logs, sleep, activity, recommendation engine
│   ├── profile.ts         # user profile CRUD
│   └── index.ts           # barrel export
│
├── components/
│   ├── common/
│   │   ├── Alert.tsx      # success / error / warning / info banners
│   │   ├── Badge.tsx      # status + priority badges
│   │   ├── Button.tsx     # primary / secondary / ghost / danger variants
│   │   ├── Card.tsx       # card + CardHeader + CardTitle
│   │   ├── EmptyState.tsx # empty list placeholder
│   │   ├── Input.tsx      # labelled input with icon + error
│   │   ├── Modal.tsx      # backdrop modal with keyboard close
│   │   ├── ProgressBar.tsx# animated progress bar
│   │   ├── ScoreRing.tsx  # SVG animated health score ring
│   │   ├── Select.tsx     # labelled select with error
│   │   ├── Spinner.tsx    # loading spinner + PageSpinner
│   │   ├── StatCard.tsx   # metric card with trend indicator
│   │   ├── Tabs.tsx       # accessible tab bar
│   │   ├── Tooltip.tsx    # hover tooltip with placement
│   │   └── index.ts       # barrel export
│   │
│   ├── charts/
│   │   ├── BarChart.tsx         # recharts bar chart wrapper
│   │   ├── HealthTrendChart.tsx # line chart for score trend
│   │   ├── MetricRadarChart.tsx # radar chart for sub-scores
│   │   └── index.ts
│   │
│   └── layout/
│       ├── AppLayout.tsx   # authenticated wrapper (redirects if logged out)
│       ├── AuthLayout.tsx  # public wrapper (redirects if logged in)
│       ├── Sidebar.tsx     # desktop nav sidebar
│       ├── TopBar.tsx      # mobile hamburger nav
│       └── index.ts
│
├── hooks/
│   ├── useAuth.ts          # login / register / logout + navigation
│   ├── useDebounce.ts      # debounce any value
│   ├── useHealthData.ts    # fetch logs + generate insights
│   ├── useLocalStorage.ts  # type-safe localStorage with cross-tab sync
│   └── index.ts
│
├── pages/
│   ├── LoginPage.tsx          # email + password form
│   ├── RegisterPage.tsx       # signup with password strength meter
│   ├── DashboardPage.tsx      # score ring, metric cards, trend chart
│   ├── HealthFormPage.tsx     # sliders + numeric inputs for all 6 metrics
│   ├── RecommendationsPage.tsx# filterable cards with expandable actions
│   ├── ProfilePage.tsx        # view/edit profile + BMI gauge + goals
│   └── NotFoundPage.tsx       # 404 with back navigation
│
├── store/
│   ├── authStore.ts    # Zustand: user, tokens, isAuthenticated
│   ├── healthStore.ts  # Zustand: logs, insights, loading flags
│   └── index.ts
│
├── types/
│   ├── index.ts        # all domain types: User, HealthLog, Recommendation…
│   └── api.ts          # API request/response types, pagination, JWT payload
│
├── utils/
│   ├── index.ts        # cn(), formatDate(), scoreColor(), getApiError()…
│   ├── formatters.ts   # fmtHours(), fmtSteps(), fmtMetricValue()…
│   ├── validators.ts   # strongPassword(), validateLogin(), inRange()…
│   └── constants.ts    # METRIC_LIMITS, SCORE_BANDS, ROUTES, LS_KEYS…
│
├── App.tsx             # BrowserRouter + all routes
├── main.tsx            # ReactDOM.createRoot
└── index.css           # Tailwind directives + custom component classes
```

---

## Pages

| Route | Page | Auth | Description |
|---|---|---|---|
| `/login` | LoginPage | Public | Email + password sign-in |
| `/register` | RegisterPage | Public | Sign-up with password strength meter |
| `/dashboard` | DashboardPage | Protected | Score ring, 6 metric cards, trend chart, quick insights |
| `/health-form` | HealthFormPage | Protected | Log all 6 daily health metrics with sliders + steppers |
| `/recommendations` | RecommendationsPage | Protected | Filterable recommendation cards with expandable action steps |
| `/profile` | ProfilePage | Protected | View/edit personal details, body metrics, BMI, health goals |
| `*` | NotFoundPage | — | 404 with back navigation |

---

## Quick Start

### Local development

```bash
cp .env.example .env
npm install
npm run dev
# → http://localhost:5173
```

### With Docker (full stack)

```bash
# Build and run frontend only
docker build -t health-frontend .
docker run -p 3000:80 health-frontend

# Full stack (frontend + api + db)
docker compose up --build
# Frontend → http://localhost:3000
# API      → http://localhost:8000/docs
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `/api/v1` | FastAPI backend base URL |

In development, Vite proxies `/api` → `http://localhost:8000` (see `vite.config.ts`).

---

## Authentication Flow

```
Register / Login
  → POST /auth/signup or /auth/login
  → store access_token + refresh_token in localStorage + Zustand

Every API request
  → Axios interceptor adds: Authorization: Bearer <access_token>

401 response
  → Axios interceptor auto-calls POST /auth/refresh
  → Swaps tokens and retries original request
  → If refresh fails → clearAuth() → redirect /login

Logout
  → POST /auth/logout (revokes refresh token server-side)
  → clearAuth() → localStorage cleared → redirect /login
```

---

## Key Components

### ScoreRing
SVG animated ring showing the 0–100 health score with colour-coded zones.

```tsx
<ScoreRing score={78} size={144} strokeWidth={12} />
```

### MetricRadarChart
Recharts radar showing all 6 metric sub-scores simultaneously.

```tsx
<MetricRadarChart metrics={insights.metric_statuses} height={240} />
```

### HealthTrendChart
Line chart showing health score over the last 14 days.

```tsx
<HealthTrendChart data={trendData} height={200} />
```

### Modal
Accessible dialog with backdrop, Escape key, focus management, and body scroll lock.

```tsx
<Modal open={open} onClose={() => setOpen(false)} title="Confirm" footer={<Button>OK</Button>}>
  Content here
</Modal>
```

---

## Adding a New Page

1. Create `src/pages/MyPage.tsx`
2. Add a route in `src/App.tsx` inside `<AppLayout>` (protected) or `<AuthLayout>` (public)
3. Add a nav entry in `src/components/layout/Sidebar.tsx` and `TopBar.tsx`
4. Export from the page file with a named export: `export function MyPage() {}`

---

## Connecting to Backend

All API calls route through `src/api/client.ts` (Axios instance).

```ts
// src/api/my-feature.ts
import apiClient from './client'

export const myApi = {
  getData: async () => {
    const res = await apiClient.get('/my-endpoint')
    return res.data
  }
}
```

The proxy in `vite.config.ts` forwards `/api/*` to `http://localhost:8000` in development.
In production, nginx forwards `/api/` to the FastAPI container (see `nginx.conf`).
