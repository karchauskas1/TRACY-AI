# FIXES

## Click Events Not Working

Problem: No click logs in production, buttons/cards not clickable

Root Cause:
- Client components verified (use client present)
- No global click probe was installed
- No ClientAlive markers to verify hydration

Fix:
- Created GlobalClickProbe component with throttled window listeners (1 log/sec max)
- Added ClientAlive markers in assistant/login components
- Added Find blocker button in debug=1 mode
- All global listeners have cleanup in useEffect return

Files:
- web-app/components/GlobalClickProbe.tsx (new)
- web-app/app/layout.tsx
- web-app/app/assistant/page.tsx
- web-app/app/login/page.tsx
- web-app/components/DebugOverlay.tsx

Test:
- Check console for [ClickProbe] logs on any tap
- Check [ClientAlive] logs on page mount
- Use Find blocker button to detect overlay elements

## Session Management

Problem: Session stored only in localStorage

Root Cause:
- No httpOnly cookie for secure session storage

Fix:
- /api/auth/telegram now sets httpOnly cookie tracy_session
- Cookie expires in 7 days, secure in production
- Created /api/me endpoint for session verification
- localStorage kept for backward compatibility

Files:
- web-app/app/api/auth/telegram/route.ts
- web-app/app/api/me/route.ts (new)
- web-app/app/login/page.tsx

Session Storage:
- httpOnly cookie: tracy_session (server-side)
- localStorage: telegram_user (client-side, for compatibility)

Verification:
- GET /api/me checks tracy_session cookie
- TODO: Store sessionId -> userData mapping in DB/Redis

Post-fix:
- Bot restarted: systemctl restart tracy-bot.service
- Production deploy: https://tracy-ai.vercel.app
