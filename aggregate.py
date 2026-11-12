"""Collect attributed headlines from RSS feeds, publish static JSON for Israel Watch."""
import calendar
import datetime as dt
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urlsplit, parse_qs, unquote

import feedparser
import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'news.json'
UTC = dt.timezone.utc
CATEGORIES = {
    'Top Stories': 'Israel Jewish people latest news',
    'US & Israel': 'US foreign policy Israel Congress State Department',
    'Israeli Politics': 'Israel Knesset government elections courts',
    'Iran & Proxies': 'Israel Iran Hamas Hezbollah Houthis security',
    'Jewish World': 'Jewish communities worldwide antisemitism diaspora',
    'Christians & Jews': 'Christian Jewish relations Israel interfaith Messianic',
    'South Africa & ICJ': 'South Africa Israel ICJ genocide case international court justice',
    'Innovation & Good News': 'Israeli innovation technology agriculture desalination investment exports breakthrough',
    'Partners Doing Good': 'Bridges for Peace FIRM Israel One For Israel humanitarian ministry',
}
# Publisher-direct feeds appear alongside a broad geographic source mix via Google News RSS.
FEEDS = [
    ('Top Stories', 'Times of Israel', 'https://www.timesofisrael.com/feed/'),
    ('Top Stories', 'The Jerusalem Post', 'https://www.jpost.com/rss/rssfeedsfrontpage.aspx'),
    ('Jewish World', 'Jewish Telegraphic Agency', 'https://www.jta.org/feed'),
    ('Innovation & Good News', 'Israel21c', 'https://www.israel21c.org/feed/'),
    ('Partners Doing Good', 'Bridges for Peace', 'https://www.bridgesforpeace.com/feed/'),
    ('Partners Doing Good', 'FIRM', 'https://firmisrael.org/feed/'),
    ('Partners Doing Good', 'ONE FOR ISRAEL', 'https://www.oneforisrael.org/feed/'),
]
for category, query in CATEGORIES.items():
    q = quote(query + ' when:7d')
    FEEDS.append((category, 'Google News aggregation', f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'))
for org, domain in [('Bridges for Peace','bridgesforpeace.com'), ('FIRM','firmisrael.org'),('ONE FOR ISRAEL','oneforisrael.org')]:
    FEEDS.append(('Partners Doing Good', f'{org} coverage', f'https://news.google.com/rss/search?q={quote("site:"+domain+" when:30d")}&hl=en-US&gl=US&ceid=US:en'))

HEADERS = {'User-Agent': 'IsraelWatch/1.0 (+public news feed aggregator; no scraping)', 'Accept': 'application/rss+xml, application/xml, text/xml, */*'}
now = dt.datetime.now(UTC)
items = []
errors = []
session = requests.Session()


def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', str(s or ''))).strip()


def date_of(entry):
    v = entry.get('published_parsed') or entry.get('updated_parsed')
    try:
        return dt.datetime.fromtimestamp(calendar.timegm(v), UTC) if v else None
    except Exception:
        return None


def publisher(entry, label):
    source = entry.get('source')
    if isinstance(source, dict) and source.get('title'):
        return clean(source['title'])
    title = clean(entry.get('title', ''))
    if ' - ' in title and label.endswith(('aggregation','coverage')):
        return title.rsplit(' - ', 1)[-1]
    return label

for category, label, url in FEEDS:
    try:
        response = session.get(url, timeout=13, headers=HEADERS)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if not feed.entries:
            raise ValueError('No entries returned')
        for entry in feed.entries[:35]:
            title = clean(entry.get('title'))
            link = entry.get('link', '').strip()
            if not title or not link or urlsplit(link).scheme not in ('https', 'http'):
                continue
            pub = publisher(entry, label)
            if label.endswith(('aggregation', 'coverage')) and title.endswith(' - ' + pub):
                title = title[:-(len(pub) + 3)]
            timestamp = date_of(entry)
            if timestamp and timestamp < now - dt.timedelta(days=21) and category != 'Partners Doing Good':
                continue
            if timestamp and timestamp > now + dt.timedelta(hours=2):
                continue
            # No re-hosted article text: links direct readers to publisher's story.
            items.append({
                'title': title[:230], 'url': link, 'source': pub[:90],
                'category': category,
                'published': timestamp.isoformat() if timestamp else None,
                'feed': label,
            })
    except Exception as exc:
        errors.append({'feed': label, 'category': category, 'error': str(exc)[:130]})

# Same headline may appear in multiple sections or feeds; retain multiple categories.
unique = {}
for it in items:
    key = re.sub(r'[^a-z0-9]', '', it['title'].lower())[:155]
    if key in unique:
        record = unique[key]
        if it['category'] not in record['categories']:
            record['categories'].append(it['category'])
        if record['feed'] == 'Google News aggregation' and it['feed'] != 'Google News aggregation':
            it['categories'] = record['categories']
            unique[key] = it
    else:
        it['categories'] = [it['category']]
        unique[key] = it

result = sorted(unique.values(), key=lambda r: r['published'] or '', reverse=True)[:700]
for it in result:
    it.pop('category', None)
OUT.parent.mkdir(parents=True, exist_ok=True)
previous = {}
if OUT.exists():
    try: previous = json.loads(OUT.read_text())
    except Exception: pass
# Preserve previous snapshot in case all feeds fail, but disclose failure prominently.
if not result and previous.get('articles'):
    result = previous['articles']
status = 'ok' if result and not errors else ('partial' if result else 'failed')
OUT.write_text(json.dumps({
    'generated_at': now.isoformat(), 'status': status,
    'article_count': len(result), 'feed_count': len(FEEDS),
    'feed_failures': errors, 'articles': result,
}, ensure_ascii=False, indent=2))
print(f'Generated {len(result)} articles from {len(FEEDS)} feeds; failures: {len(errors)}')
