# FIXES

## Telegram Login

Problem: Button "Войти через Telegram" not working in Mini App

Root Cause:
- No button for manual auth in Telegram Mini App
- No backend endpoint for initData verification
- useSearchParams not wrapped in Suspense

Fix:
- Added button with handleTelegramLogin handler
- Created /api/auth/telegram endpoint with HMAC SHA256 verification
- Wrapped useSearchParams in Suspense boundary
- Added debug logging for clicks (debug=1 mode)

Files:
- web-app/app/api/auth/telegram/route.ts (new)
- web-app/app/login/page.tsx

Endpoint: POST /api/auth/telegram
- Verifies initData signature using Bot Token
- Returns user data on success

Session: Stored in localStorage as telegram_user JSON

Test:
- Mobile/Desktop Telegram: Click button → auth → redirect to /assistant
- Check localStorage for real userId (not "demo")
