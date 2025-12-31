from post_current_events import run as post_current_events
from rss_ingest import run as ingest_rss
from rss_feeds import FEED_URLS
import sys

FIREBASE_BASE_URL="https://digest-a3589-default-rtdb.firebaseio.com"

def main():
    try:
        post_current_events(FIREBASE_BASE_URL)
    except Exception as e:
        print(f"Error in post_current_events: {e}", file=sys.stderr)
        raise
    
    try:
        count = ingest_rss(FEED_URLS, FIREBASE_BASE_URL)
        print(f"RSS ingest completed: {count} items posted")
    except Exception as e:
        print(f"Error in ingest_rss: {e}", file=sys.stderr)
        raise

if __name__=="__main__":
    main()