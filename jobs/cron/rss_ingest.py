import requests, feedparser, secrets
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import sys

def generate_unique_id():
    return secrets.randbelow(9000000000) + 1000000000

def _dt_from_struct(t):
    if not t: return None
    try:
        return datetime(*t[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError) as e:
        print(f"Error parsing time struct: {e}, struct: {t}", file=sys.stderr)
        return None

def _entry_time(e):
    return _dt_from_struct(getattr(e, "published_parsed", None)) or _dt_from_struct(getattr(e, "updated_parsed", None))

def _post_json(url, payload):
    try:
        r=requests.post(url, json=payload, timeout=20)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"Error posting to Firebase: {e}, URL: {url}, Title: {payload.get('title', 'n/a')}", file=sys.stderr)
        raise

def _fetch_feed(url):
    try:
        r=requests.get(url, timeout=25, headers={"User-Agent":"cron-rss/1.0"})
        r.raise_for_status()
        parsed = feedparser.parse(r.text)
        # Check for feedparser errors
        if parsed.bozo and parsed.bozo_exception:
            print(f"Warning: Feed parsing issue for {url}: {parsed.bozo_exception}", file=sys.stderr)
        return url, parsed
    except Exception as e:
        print(f"Error fetching feed {url}: {e}", file=sys.stderr)
        # Return None to indicate failure, caller will handle it
        return None, None

def run(feed_urls, firebase_base_url):
    now=datetime.now(timezone.utc)
    cutoff=now - timedelta(hours=24)
    print(f"RSS ingest starting: cutoff={cutoff.isoformat()}, feeds={len(feed_urls)}")

    items=[]
    feed_errors=0
    feed_success=0

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(feed_urls)))) as ex:
        futs=[ex.submit(_fetch_feed, u) for u in feed_urls]
        for f in as_completed(futs):
            try:
                feed_url, d=f.result()
                if feed_url is None or d is None:
                    feed_errors += 1
                    continue
                feed_success += 1
                entry_count = len(getattr(d, "entries", []) or [])
                print(f"Fetched {feed_url}: {entry_count} entries")
                
                for e in getattr(d, "entries", []) or []:
                    ts=_entry_time(e)
                    if not ts:
                        print(f"Skipping entry (no timestamp): {e.get('title', 'n/a')[:50]} from {feed_url}", file=sys.stderr)
                        continue
                    if ts < cutoff:
                        continue
                    items.append((feed_url, e, ts))
            except Exception as e:
                feed_errors += 1
                print(f"Failed to process feed result: {e}", file=sys.stderr)

    print(f"Total items found (within 24h): {len(items)}, successful feeds: {feed_success}, failed feeds: {feed_errors}")

    seen=set()
    deduped=[]
    for feed_url, e, ts in sorted(items, key=lambda x: x[2].isoformat()):
        k=e.get("id") or e.get("guid") or e.get("link")
        if not k:
            print(f"Skipping entry (no id/guid/link): {e.get('title', 'n/a')[:50]} from {feed_url}", file=sys.stderr)
            continue
        if k in seen:
            continue
        seen.add(k)
        deduped.append((feed_url, e, ts))

    print(f"After deduplication: {len(deduped)} items to post")

    posted=0
    post_errors=0
    for feed_url, e, ts in deduped:
        try:
            unique_id=generate_unique_id()
            post_url=f"{firebase_base_url}/{unique_id}.json"

            source=urlparse(feed_url).netloc or "n/a"
            payload={
                "category":"News",
                "title": e.get("title") or "n/a",
                "metadata": f"feed_url={feed_url}",
                "link": e.get("link") or "n/a",
                "summary": e.get("summary") or e.get("description") or "n/a",
                "source": source,
                "date": ts.isoformat(),
            }

            _post_json(post_url, payload)
            posted += 1
        except Exception as e:
            post_errors += 1
            print(f"Failed to post entry: {e}, Title: {payload.get('title', 'n/a')[:50]}", file=sys.stderr)

    print(f"RSS ingest (24h cap, stateless): written={posted}, errors={post_errors}")
    return posted