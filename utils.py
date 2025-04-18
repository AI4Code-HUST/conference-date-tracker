import json
import re
import os
from ics import Event
from datetime import (
    datetime,
    timezone,
    timedelta,
    date
)

MONTH_DICT = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}
AOE_TZ = timezone(timedelta(hours=-12))

SERVICE_ACCOUNT_FILE = ".credentials/service_client.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "c1c3cc42b9be97acffa4fb3bcb785cd4f57aa914fbbdf8698b349c429ebf17c3@group.calendar.google.com"
APP_PASSWORD = os.getenv("APP_PASSWORD")
SENDER = "ai4code.hust@gmail.com"

try:
    with open('filter_config.json', 'r') as filter_file:
        filters = json.load(filter_file)
except Exception as e:
    filters = {}

def extract_row_element_text(td):
    if td.text:
        return td.text
    else:
        return td.find("strong").text
    
def get_date(event_date):
    # Find Hour::Minute
    hour_minute = re.search(r"\d{1,2}:\d{1,2}", event_date)
    if hour_minute:
        hour_minute = hour_minute.group()
        event_date = event_date.replace(hour_minute, "")
    
    hour = int(hour_minute.split(":")[0]) if hour_minute else None
    minute = int(hour_minute.split(":")[1]) if hour_minute else None

    # Find year
    year = re.search(r"\d{4}", event_date)
    if year:
        year = year.group()
        event_date = event_date.replace(year, "")

    # Find month
    month = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", event_date)
    if month:
        month = month.group()
        event_date = event_date.replace(month, "")

    # Find day
    day = re.search(r"\d{1,2}", event_date)
    if day:
        day = day.group()
        event_date = event_date.replace(day, "")

    return year, month, day, hour, minute
    
def create_event(event_conference, event_conference_link, event_date, event_track, event_content, event_link):
    event = Event()
    
    event.name = event_conference + " - " + event_track + " - " + event_content
    event.description = f"""
        Conference: {event_conference}
        Conference Link: {event_conference_link}
        Date: {event_date}
        Track: {event_track}
        Event Link: {event_link}
    """
    event_date = event_date.strip()

    # Only 1 day event:
    if '-' not in event_date:
        year, month, day, _, _ = get_date(event_date)
        event.begin = datetime(int(year), MONTH_DICT[month], int(day), 0, 0).replace(tzinfo=AOE_TZ)
        event.end = (datetime(int(year), MONTH_DICT[month], int(day), 23, 59) + timedelta(minutes=1)).replace(tzinfo=AOE_TZ)

        return event
    else:
        start_date, end_date = event_date.split("-")

        # Get year, month, day, hour and minute
        start_year, start_month, start_day, start_hour, start_minute = get_date(start_date)
        end_year, end_month, end_day, end_hour, end_minute = get_date(end_date)

        # If start year, month and day are None, set them to end year, month and day and vice versa
        start_year = start_year if start_year else end_year
        end_year = end_year if end_year else start_year

        start_month = start_month if start_month else end_month
        end_month = end_month if end_month else start_month

        start_day = start_day if start_day else end_day
        end_day = end_day if end_day else start_day

        # Set default values if they are None
        start_hour = 0 if start_hour is None else start_hour
        start_minute = 0 if start_minute is None else start_minute
        end_hour = 23 if end_hour is None else end_hour
        end_minute = 59 if end_minute is None else end_minute

        event.begin = datetime(int(start_year), MONTH_DICT[start_month], int(start_day), start_hour, start_minute).replace(tzinfo=AOE_TZ)
        event.end = (datetime(int(end_year), MONTH_DICT[end_month], int(end_day), end_hour, end_minute) + timedelta(minutes=1)).replace(tzinfo=AOE_TZ)

        return event
    
def check_filter(event_conference, event_date, event_track, event_content):
    event_conference = re.sub(r'\b-?\d{4}\b', '', event_conference).strip()
    event_track = event_track.strip()
    event_content = event_content.strip()
    year, month, day, _, _ = get_date(event_date)
    event_date = date(int(year), MONTH_DICT[month], int(day))

    # Check if upcoming duration is allowed
    upcoming_delta = timedelta(days=filters['upcoming_duration']['day'] + filters['upcoming_duration']['month'] * 30 + filters['upcoming_duration']['year'] * 365)
    if event_date < date.today() or event_date > date.today() + upcoming_delta:
        return False
    
    # Check if conference is allowed
    if event_conference not in filters['conference_filter'] or not filters['conference_filter'][event_conference]:
        return False
    
    # Check if track is allowed
    if event_track not in filters['track_filter'][event_conference] or not filters['track_filter'][event_conference][event_track]:
        return False
    
    # Check if content is allowed
    if event_content not in filters['content_filter'] or not filters['content_filter'][event_content]:
        return False
    
    return True


def update_filter(events):
    # Filter Upcoming duration
    if 'upcoming_duration' not in filters:
        filters['upcoming_duration'] = {
            "year": 1,
            "month": 0,
            "day": 0
        }

    # Filter Conferences
    if 'conference_filter' not in filters:
        filters['conference_filter'] = {}

    current_conferences = set()

    for event in events:
        conference_name = re.sub(r'\b-?\d{4}\b', '', event['conference']).strip()
        current_conferences.add(conference_name)

    for conference in current_conferences:
        if conference not in filters['conference_filter']:
            filters['conference_filter'][conference] = False
            log_notification(f"New conference updated in the filter: {conference}")

    filters['conference_filter'] = {k: v for k, v in sorted(filters['conference_filter'].items())}

    # Filter Tracks
    if 'track_filter' not in filters:
        filters['track_filter'] = {}

    for conference in filters['conference_filter']:
        if conference not in filters['track_filter']:
            filters['track_filter'][conference] = {}
        
        tracks = set()
        for event in events:
            if event['conference'].startswith(conference):
                tracks.add(event['track'])

        for track in tracks:
            if track not in filters['track_filter'][conference]:
                filters['track_filter'][conference][track] = False
                log_notification(f"New track updated in the filter: {conference} - {track}")

        filters['track_filter'][conference] = {k: v for k, v in sorted(filters['track_filter'][conference].items())}

    # Filter Contents
    if 'content_filter' not in filters:
        filters['content_filter'] = {}

    for event in events:
        content = event['content']
        if content not in filters['content_filter']:
            filters['content_filter'][content] = False
            log_notification(f"New content updated in the filter: {content}")

    filters['content_filter'] = {k: v for k, v in sorted(filters['content_filter'].items())}

    # Export the filters
    with open('filter_config.json', 'w') as filter_file:
        json.dump(filters, filter_file, indent=4)

def log_notification(message):
    print(message)
    with open("notification.log", "a") as f:
        f.write(f"{message}\n")

def sort_by_date(conference_events):
    """
    Sort a list of conference event dictionaries by the 'date' field.
    
    Args:
        conference_events (list): List of dicts, each containing a 'date' key.

    Returns:
        list: Sorted list of dictionaries by date.
    """
    for event in conference_events:
        try:
            # Handle date ranges (e.g., "Mon 10 - Thu 13 Nov 2025")
            if '-' in event['date']:
                log_notification(f"Handling date range for event: {event}")
                start_date, end_date = event['date'].split('-')
                start_date = start_date.strip()
                end_date = end_date.strip()

                # Extract month and year from the end_date if missing in start_date
                if not re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", start_date):
                    month = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", end_date).group()
                    start_date += f" {month}"
                if not re.search(r"\d{4}", start_date):
                    year = re.search(r"\d{4}", end_date).group()
                    start_date += f" {year}"

                event['date'] = start_date

            # Remove time part if present
            if ':' in event['date']:
                log_notification(f"Invalid date format for event: {event}")
                event['date'] = re.sub(r"\b\d{1,2}:\d{2}\b", "", event['date']).strip()
            
            event['date'] = datetime.strptime(event['date'], "%a %d %b %Y").strftime("%a %d %b %Y")
        except ValueError:
            log_notification(f"Invalid date format for event: {event}")
    return sorted(conference_events, key=lambda x: datetime.strptime(x['date'], "%a %d %b %Y"))
