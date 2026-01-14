# FIXES

## Telegram Login Button

Problem: Button "Войти через Telegram" not working in demo mode

Root Cause:
- Button rendered correctly (Button component)
- No overlay/z-index issues
- Auth endpoint exists

Fix:
- Button handler calls handleTelegramLogin
- Endpoint /api/auth/telegram verifies initData via HMAC SHA256
- Session stored in localStorage as telegram_user
- Wrapped useSearchParams in Suspense

Files:
- web-app/app/login/page.tsx
- web-app/app/api/auth/telegram/route.ts

Test:
- Click button in Telegram Mini App → handleTelegramLogin → verify initData → redirect to /assistant

## Card Clicks After Return

Problem: Cards on /assistant stop working after returning from other pages

Root Cause:
- preventDefault() and stopPropagation() on card onClick handlers blocked events
- setTimeout fallback navigation violated requirements

Fix:
- Removed preventDefault/stopPropagation from all card onClick handlers
- Removed setTimeout fallback navigation
- Simplified handlers to direct router.push() calls
- Added debug diagnostics (debug=1): event counters, lastClick, lastNavAttempt
- Wrapped useSearchParams in Suspense

Files:
- web-app/app/assistant/page.tsx

Test:
- Navigate /assistant → /chat → back → /assistant → click cards → should navigate
- Check debug=1 overlay for event counts and navigation attempts

Post-fix:
- Bot restarted: systemctl restart tracy-bot.service
- Production deploy: https://tracy-ai.vercel.app
