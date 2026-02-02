#!/usr/bin/env python3
"""
End-to-end verification test script for event deletion feature
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        from conversation_handler import ConversationHandler
        print("✅ conversation_handler.py imports successfully")
    except Exception as e:
        print(f"❌ Failed to import conversation_handler: {e}")
        return False

    try:
        from calendar_google import GoogleCalendar
        print("✅ GoogleCalendar imports successfully")
    except Exception as e:
        print(f"❌ Failed to import GoogleCalendar: {e}")
        return False

    try:
        from calendar_icloud import ICloudCalendar
        print("✅ ICloudCalendar imports successfully")
    except Exception as e:
        print(f"❌ Failed to import ICloudCalendar: {e}")
        return False

    return True

def test_implementation():
    """Verify the implementation exists in conversation_handler.py"""
    print("\nVerifying implementation...")

    with open('./conversation_handler.py', 'r') as f:
        content = f.read()

    # Check for Google Calendar deletion
    if 'GoogleCalendar(user_id)' in content and 'delete_event(event[\'external_id\'])' in content:
        print("✅ Google Calendar deletion implementation found")
    else:
        print("❌ Google Calendar deletion implementation missing")
        return False

    # Check for iCloud Calendar deletion
    if 'ICloudCalendar(' in content and 'caldav_url' in content:
        print("✅ iCloud Calendar deletion implementation found")
    else:
        print("❌ iCloud Calendar deletion implementation missing")
        return False

    # Check for proper imports
    if 'from calendar_google import GoogleCalendar' in content:
        print("✅ GoogleCalendar import found")
    else:
        print("❌ GoogleCalendar import missing")
        return False

    if 'from calendar_icloud import ICloudCalendar' in content:
        print("✅ ICloudCalendar import found")
    else:
        print("❌ ICloudCalendar import missing")
        return False

    if 'import json' in content:
        print("✅ json import found")
    else:
        print("❌ json import missing")
        return False

    return True

if __name__ == '__main__':
    print("="*60)
    print("Event Deletion Implementation Verification")
    print("="*60)

    imports_ok = test_imports()
    impl_ok = test_implementation()

    print("\n" + "="*60)
    if imports_ok and impl_ok:
        print("✅ All automated checks passed!")
        print("\nReady for manual E2E testing:")
        print("1. Run: python3 bot.py")
        print("2. Follow the manual verification steps")
        sys.exit(0)
    else:
        print("❌ Some checks failed")
        sys.exit(1)
