from post_current_events import run as post_current_events
from rss_ingest import run as ingest_rss
from rss_feeds import FEED_URLS

FIREBASE_BASE_URL="https://digest-a3589-default-rtdb.firebaseio.com"

def main():
    post_current_events(FIREBASE_BASE_URL)
    ingest_rss(FEED_URLS, FIREBASE_BASE_URL)

if __name__=="__main__":
    main()