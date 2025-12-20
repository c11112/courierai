from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests, secrets

def generate_unique_id():
    return secrets.randbelow(9000000000) + 1000000000

def run(firebase_base_url):
    unique_id=generate_unique_id()
    post_url=f"{firebase_base_url}/{unique_id}.json"

    now=datetime.now(ZoneInfo("America/New_York"))
    current_date=(now - timedelta(days=1)).strftime("%Y_%B_%-d")

    payload={
        "category":"News",
        "title":"Current Events Summary",
        "metadata":"n/a",
        "link":f"https://en.wikipedia.org/wiki/Portal:Current_events/{current_date}",
        "summary":"n/a",
        "source":"n/a",
        "date":"n/a",
    }

    r=requests.post(post_url, json=payload, timeout=20)
    r.raise_for_status()
    print(f"Posted current events stub: {r.status_code}")