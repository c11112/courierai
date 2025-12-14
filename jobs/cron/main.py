from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import secrets

def generate_unique_id():
    return secrets.randbelow(9000000000) + 1000000000

unique_id = generate_unique_id()

post_url = f'https://digest-a3589-default-rtdb.firebaseio.com/{unique_id}.json'

current_date = (datetime.now() - timedelta(days=1)).strftime("%Y_%B_%-d")
category = "News"
title = "Current Events Summary"
link = f'https://en.wikipedia.org/wiki/Portal:Current_events/{current_date}'
summary = "n/a"
date = "n/a"
source = "n/a"
metadata = "n/a"
    
payload = {
    "category": category,
    "title": title,
    "metadata": metadata,
    "link": link,
    "summary": summary,
    "source": source,
    "date": date
    }

response = requests.post(post_url, json=payload)
response.raise_for_status()
print(f"Successfully posted payload: {response.status_code}")
