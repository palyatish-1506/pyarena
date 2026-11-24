# 0002 — JWT delivery: httpOnly cookies, not localStorage

## Context
Milestone 1 adds auth. SimpleJWT's default flow returns access/refresh tokens
in the JSON body; the frontend then chooses where to keep them. The two
standard options are `localStorage` (readable by any JS on the page) and
`httpOnly` cookies (invisible to JavaScript).

## Decision
Tokens live in **httpOnly cookies** set by the backend. The frontend never
sees them — the browser attaches them automatically to same-site/cross-site
requests (`withCredentials` on Axios). A custom DRF authentication class reads
the `access_token` cookie; a refresh endpoint rotates the `refresh_token`
cookie.

## Alternatives considered
- **localStorage + Bearer header** — simpler (no cookie auth class, no
  SameSite/Secure config) but any XSS bug exfiltrates tokens. Rejected by the
  owner; cookies are the stronger pattern for a real product.
- **Hybrid (cookie + bearer)** — more code paths, no benefit here.

## Consequences
- Need a custom `CookieJWTAuthentication` (DRF's JWTAuthentication only reads
  the `Authorization` header).
- Cross-site prod (vercel.app → onrender.com) requires
  `SameSite=None; Secure` cookies; dev uses `SameSite=Lax` without Secure —
  both env-configurable.
- CORS must allow credentials (`CORS_ALLOW_CREDENTIALS=True`, already set)
  and the exact frontend origin (already configured).
- CSRF: not applicable — we authenticate via JWT cookie, not Django sessions,
  and DRF only enforces CSRF for SessionAuthentication.
- Logout = delete cookies server-side.
- Refresh rotation + blacklist (already enabled in SIMPLE_JWT settings)
  works unchanged — the refresh token travels by cookie.
