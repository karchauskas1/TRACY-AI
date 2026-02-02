# End-to-End Verification Checklist
## Event Deletion Feature for Google Calendar and iCloud

**Task:** Subtask-2-1 - End-to-end verification of deletion workflow
**Date:** 2026-02-01
**Status:** Ready for Manual Testing

---

## ✅ Automated Verification (COMPLETED)

- [x] Code structure verified in conversation_handler.py
- [x] Google Calendar deletion implementation present (lines 309-311)
- [x] iCloud Calendar deletion implementation present (lines 313-328)
- [x] Required imports present (GoogleCalendar, ICloudCalendar, json)
- [x] Error handling in place (try/except block)
- [x] Database cleanup calls present (delete_reminders_for_event, delete_event)
- [x] Logging statements added for tracking

---

## 📋 Manual E2E Testing Steps

### Prerequisites
- [ ] Telegram bot is configured and running
- [ ] Google Calendar is connected to the bot
- [ ] (Optional) iCloud Calendar is connected to the bot

---

### Test 1: Google Calendar Event Deletion

#### Step 1.1: Create Test Event
- [ ] Open Telegram and send message to bot:
  ```
  Create meeting tomorrow at 3pm called Test Delete Google
  ```
- [ ] **Expected:** Bot confirms event creation
- [ ] **Verify:** Event appears in Google Calendar web interface
- [ ] **Screenshot:** Take screenshot of Google Calendar showing the event

#### Step 1.2: Delete Event via Bot
- [ ] Send message to bot:
  ```
  Delete Test Delete Google
  ```
- [ ] **Expected:** Bot shows confirmation message with event details
- [ ] **Expected:** Bot asks for confirmation (e.g., "Type 1 to confirm")
- [ ] **Screenshot:** Take screenshot of confirmation message

#### Step 1.3: Confirm Deletion
- [ ] Send confirmation (e.g., type "1" or "yes")
- [ ] **Expected:** Bot confirms deletion with success message
- [ ] **Expected:** Message includes "✓ Событие удалено из Google Calendar"

#### Step 1.4: Verify Deletion in Calendar
- [ ] Refresh Google Calendar web interface
- [ ] **Expected:** Event "Test Delete Google" is no longer visible
- [ ] **Screenshot:** Take screenshot showing event is gone

#### Step 1.5: Verify Database Cleanup
- [ ] Check bot logs for:
  ```
  ✓ Событие удалено из Google Calendar: [event_id]
  ```
- [ ] **Expected:** Log entry confirms external calendar deletion
- [ ] **Expected:** No errors in logs

---

### Test 2: iCloud Calendar Event Deletion (If iCloud Connected)

#### Step 2.1: Create Test Event
- [ ] Send message to bot:
  ```
  Create meeting tomorrow at 4pm called Test Delete iCloud
  ```
- [ ] **Expected:** Bot confirms event creation
- [ ] **Verify:** Event appears in iCloud Calendar
- [ ] **Screenshot:** Take screenshot of iCloud Calendar showing the event

#### Step 2.2: Delete Event via Bot
- [ ] Send message to bot:
  ```
  Delete Test Delete iCloud
  ```
- [ ] **Expected:** Bot shows confirmation message with event details
- [ ] **Expected:** Bot asks for confirmation
- [ ] **Screenshot:** Take screenshot of confirmation message

#### Step 2.3: Confirm Deletion
- [ ] Send confirmation
- [ ] **Expected:** Bot confirms deletion with success message
- [ ] **Expected:** Message includes "✓ Событие удалено из iCloud Calendar"

#### Step 2.4: Verify Deletion in Calendar
- [ ] Refresh iCloud Calendar interface
- [ ] **Expected:** Event "Test Delete iCloud" is no longer visible
- [ ] **Screenshot:** Take screenshot showing event is gone

#### Step 2.5: Verify Database Cleanup
- [ ] Check bot logs for:
  ```
  ✓ Событие удалено из iCloud Calendar: [event_uid]
  ```
- [ ] **Expected:** Log entry confirms external calendar deletion
- [ ] **Expected:** No errors in logs

---

### Test 3: Error Handling - Non-existent Event

#### Step 3.1: Try to Delete Non-existent Event
- [ ] Send message to bot:
  ```
  Delete NonExistentEvent12345
  ```
- [ ] **Expected:** Bot shows error message
- [ ] **Expected:** Message indicates event not found (e.g., "❌ Событие не найдено")
- [ ] **Expected:** No crash or unexpected behavior
- [ ] **Screenshot:** Take screenshot of error message

---

### Test 4: Edge Cases

#### Step 4.1: Delete Event Without Confirmation
- [ ] Create another test event
- [ ] Start deletion process but cancel instead of confirming
- [ ] **Expected:** Event remains in calendar
- [ ] **Expected:** Bot handles cancellation gracefully

#### Step 4.2: Delete Event with Reminders
- [ ] Create event with reminder
- [ ] Delete the event
- [ ] **Expected:** Event and associated reminders are both deleted
- [ ] **Verify:** Check database (if accessible) that reminders are removed

---

## 🔍 Verification Criteria

### Success Criteria (All must pass)
- [ ] Google Calendar events can be deleted via bot
- [ ] iCloud Calendar events can be deleted via bot (if configured)
- [ ] Deletion confirmation flow works correctly
- [ ] Events are removed from external calendar provider
- [ ] Events are removed from bot's database
- [ ] Reminders associated with events are deleted
- [ ] Error messages are clear and appropriate
- [ ] No crashes or unexpected errors
- [ ] Logs show successful deletion

### Code Quality Checks (Already Verified)
- [x] Follows existing code patterns from decision_engine.py
- [x] Proper error handling with try/except
- [x] Logging for success and error cases
- [x] Database cleanup (reminders + events)
- [x] External calendar API calls implemented

---

## 📝 Test Results

### Google Calendar Test
- **Status:** ⏳ Pending Manual Execution
- **Notes:** _Fill in after testing_

### iCloud Calendar Test
- **Status:** ⏳ Pending Manual Execution
- **Notes:** _Fill in after testing_

### Error Handling Test
- **Status:** ⏳ Pending Manual Execution
- **Notes:** _Fill in after testing_

---

## 🐛 Issues Found

_List any bugs or issues discovered during testing:_

1.
2.
3.

---

## ✅ Sign-off

- [ ] All manual tests executed
- [ ] All success criteria met
- [ ] No blocking issues found
- [ ] Ready to mark subtask as complete

**Tester:** _________________
**Date:** _________________

---

## 📚 Implementation Details

### Files Modified
- `conversation_handler.py` - Added event deletion implementation

### Key Changes
1. **Lines 309-311:** Google Calendar deletion
   ```python
   calendar = GoogleCalendar(user_id)
   calendar.delete_event(event['external_id'])
   logger.info(f"✓ Событие удалено из Google Calendar: {event['external_id']}")
   ```

2. **Lines 313-328:** iCloud Calendar deletion
   ```python
   calendar_connections = self.db.get_calendar_connections(user_id)
   conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
   if conn:
       credentials = json.loads(conn['credentials'])
       calendar = ICloudCalendar(
           user_id=user_id,
           caldav_url=credentials.get('caldav_url', 'https://caldav.icloud.com'),
           username=credentials.get('username'),
           password=credentials.get('password')
       )
       calendar.delete_event(event['external_id'])
       logger.info(f"✓ Событие удалено из iCloud Calendar: {event['external_id']}")
   ```

3. **Imports Added:**
   - `from calendar_google import GoogleCalendar`
   - `from calendar_icloud import ICloudCalendar`
   - `import json`

### Pattern References
- Based on `decision_engine.py:1085-1134` for calendar instantiation
- Based on `calendar_google.py:386-400` for Google deletion API
- Based on `calendar_icloud.py:307-345` for iCloud deletion API

---

## 🎯 Next Steps After Verification

1. Mark subtask-2-1 as completed in implementation_plan.json
2. Commit verification results
3. Update build-progress.txt
4. Task 003 complete!
