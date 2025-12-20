import requests, feedparser, secrets
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

def generate_unique_id():
    return secrets.randbelow(9000000000) + 1000000000

def _dt_from_struct(t):
    if not t: return None
    return datetime(*t[:6], tzinfo=timezone.utc)

def _entry_time(e):
    return _dt_from_struct(getattr(e, "published_parsed", None)) or _dt_from_struct(getattr(e, "updated_parsed", None))

def _post_json(url, payload):
    r=requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r

def _fetch_feed(url):
    r=requests.get(url, timeout=25, headers={"User-Agent":"cron-rss/1.0"})
    r.raise_for_status()
    return url, feedparser.parse(r.text)

def run(feed_urls, firebase_base_url):
    now=datetime.now(timezone.utc)
    cutoff=now - timedelta(hours=24)

    items=[]

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(feed_urls)))) as ex:
        futs=[ex.submit(_fetch_feed, u) for u in feed_urls]
        for f in as_completed(futs):
            feed_url, d=f.result()
            for e in getattr(d, "entries", []) or []:
                ts=_entry_time(e)
                if not ts or ts < cutoff:
                    continue
                items.append((feed_url, e, ts))

    seen=set()
    deduped=[]
    for feed_url, e, ts in sorted(items, key=lambda x: x[2].isoformat()):
        k=e.get("id") or e.get("guid") or e.get("link")
        if not k or k in seen:
            continue
        seen.add(k)
        deduped.append((feed_url, e, ts))

    for feed_url, e, ts in deduped:
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

    print(f"RSS ingest (24h cap, stateless): written={len(deduped)}")
    return len(deduped)