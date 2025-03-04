import concurrent.futures
import os

import requests
from bs4 import BeautifulSoup
from lxml import etree
from ics import Calendar

from utils import *
 

# Get the HTML content of the website
base_url = "https://conf.researchr.org/"
response = requests.get(base_url)


# Get all the <h3> elements that contain the conference names and links
soup = BeautifulSoup(response.text, "lxml")
dom = etree.HTML(str(soup))
conferences = dom.xpath("//div[div[@class='panel-title' and text()='Upcoming Conferences']]/..//h3")

calendar = Calendar()

# Extract the events from the conferences
def fetch_conference_events(conference):
    events = []
    conference_name = conference.find("a").text
    conference_schedule_link = conference.find("a").get("href").replace("home", "dates")

    if conference_schedule_link.startswith(base_url):
        response = requests.get(conference_schedule_link)
        soup = BeautifulSoup(response.text, "lxml")
        dom = etree.HTML(str(soup))

        tr_elements = dom.xpath("//tr[@class='clickable-row text-success']")
        for tr in tr_elements:
            
            td_elements = tr.xpath(".//td")
            
            event_conference = conference_name.strip()
            event_conference_link = conference.find("a").get("href")
            event_date = extract_row_element_text(td_elements[0]).strip()
            event_track = extract_row_element_text(td_elements[1]).strip()
            event_content = extract_row_element_text(td_elements[2]).strip()
            event_link = tr.get("href")

            event = create_event(event_conference, event_conference_link, event_date, event_track, event_content, event_link)

            events.append({
                "conference": event_conference,
                "conference_link": event_conference_link,
                "date": event_date.strip(),
                "track": event_track.strip(),
                "content": event_content.strip(),
                "link": event_link,
                "gg_calendar_href": f"https://calendar.google.com/calendar/u/0/r/eventedit?text={event.name.replace(" ", "+")}"
                                    + f"&dates={event.begin.strftime("%Y%m%dT%H%M%SZ")}/{event.end.strftime("%Y%m%dT%H%M%SZ")}"
                                    + f"&details={event.description.replace(" ", "+").replace("\n", "%0A")}&location&sprop&sprop=name:"
            })

            if check_filter(event_conference, event_date, event_track, event_content):
                calendar.events.add(event)

    return events

events = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(fetch_conference_events, conference) for conference in conferences]
    for future in concurrent.futures.as_completed(futures):
        events.extend(future.result())

# Update the filter.json file with the new events
update_filter(events)

# Sort events by date, conference, track, and content
events = sorted(events, key=lambda x: (x["date"], x["conference"], x["track"], x["content"]))

# Compare events with the old events
if os.path.exists("results/conference_events.jsonl"):
    with open("results/conference_events.jsonl", "r") as f:
        old_events = [json.loads(line) for line in f.readlines()]

        if old_events != events:
            newly_appear_conferences = set()
            for event in events:
                if event not in old_events:
                    newly_appear_conferences.add(event["conference"])

            if newly_appear_conferences:
                log_notification(f"New events found in the following conferences: {', '.join(newly_appear_conferences)}")


# Save the new events to a file
os.makedirs("results", exist_ok=True)
with open("results/conference_events.jsonl", "w") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")

# Save the conference events to a file
with open(f"results/conference_events.ics", "w") as f:
    f.writelines(calendar)

# Send notification to subcribed users
# send_notification_to_subscribed()