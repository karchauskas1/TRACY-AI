# FIXES

## Click Handlers Not Working

Problem: pointerdown events logged but onClick handlers not firing

Root Cause:
- In Telegram Mini App WebView click не приходил после tap (видели pointerdown без click → навигация/кнопки не срабатывали)
- Дополнительно диагностику путал общий throttle в ClickProbe (в non-debug мог скрывать pointerup/click как будто их нет)

Fix:
- Ensured `touch-action: manipulation` реально применяется на `html, body` (+ `-webkit-text-size-adjust: 100%`)
- Extended GlobalClickProbe: separate per-event-type logging in capture phase (debug=1 без фильтрации), плюс расширенные поля (defaultPrevented/cancelBubble/pointerType/coords)
- Added Telegram-only fallback: synth `click` on tap завершении (pointerup/touchend), если реальный click не пришёл за короткое окно
- Added debug CSS diagnostics on `/login?debug=1` (computed `touchAction` для html/body и элемента под пальцем через `elementFromPoint`)
- Minor semantics: Settings icon is a proper `<button type="button" aria-label="Settings">`

Files:
- `web-app/app/globals.css`
- `web-app/components/GlobalClickProbe.tsx`
- `web-app/app/login/page.tsx`
- `web-app/app/assistant/page.tsx`

Test:
- In Telegram with `debug=1`: one tap should log `pointerdown` + (`pointerup`/`touchend`) + `click`
- Navigation via cards/Settings should work

## Removed Old MD Reports

Deleted all old fix reports except:
- README.md
- SYSTEM_ARCHITECTURE.md
- FIXES.md (this file)

Post-fix:
- Bot restarted: systemctl restart tracy-bot.service
- Production deploy: https://tracy-ai.vercel.app
