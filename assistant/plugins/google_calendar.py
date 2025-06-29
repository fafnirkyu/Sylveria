import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = Credentials.from_authorized_user_file("config/token.json", SCOPES)
    return build('calendar', 'v3', credentials=creds)

def create_event(summary, start_time, recurring=False):
    service = get_calendar_service()

    event = {
        'summary': summary,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': (start_time + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'UTC'},
    }

    if recurring:
        event['recurrence'] = ['RRULE:FREQ=WEEKLY']

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"[Calendar] Created: {event.get('htmlLink')}")
    return event

def get_upcoming_events(days_ahead=1):
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=future,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

def find_event_by_title(title):
    events = get_upcoming_events(days_ahead=14)
    for event in events:
        if title.lower() in event.get('summary', '').lower():
            return event
    return None

def update_event(event_id, updates: dict):
    service = get_calendar_service()
    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    for key, value in updates.items():
        if key in ['start', 'end', 'summary']:
            event[key] = value

    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    print(f"[Calendar] Updated event: {updated_event['summary']}")
    return updated_event

# 🔌 Optional startup hook
def start(assistant):
    print("[Plugin] Google Calendar available. No background thread needed.")
    # If needed, you could attach functions here like:
    assistant.tools.google_calendar = {
        "create_event": create_event,
        "get_upcoming_events": get_upcoming_events,
        "find_event_by_title": find_event_by_title,
        "update_event": update_event,
    }
