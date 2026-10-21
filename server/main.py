"""Blendin: local club matching with optional bounded event discovery."""
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title='Blendin', version='1.0.0')
CLUBS = list(dict.fromkeys(json.loads((ROOT / 'data/club_links.json').read_text())))
ALIASES = {
    'sports': ['basketball', 'soccer', 'tennis', 'volleyball', 'rugby', 'rowing', 'frisbee', 'swim', 'cycling', 'running'],
    'music': ['music', 'choir', 'orchestra', 'acappella', 'jazz', 'band', 'symphony'],
    'coding': ['coding', 'programming', 'acm', 'computerscience', 'robotics'],
    'tech': ['technology', 'acm', 'computerscience', 'robotics'],
    'ai': ['artificialintelligence', 'machinelearning', 'datascience', 'acm'],
    'creative': ['art', 'design', 'photography', 'theatre', 'film'],
    'outdoor': ['outdoor', 'hiking', 'climbing', 'adventure'],
    'volunteer': ['volunteer', 'service', 'habitat', 'community'],
    'boardgames': ['boardgame', 'chess', 'gaming'],
    'fitness': ['fitness', 'running', 'yoga', 'cycling'],
}
# Fixed, publicly accessible listing pages; no arbitrary user-provided fetch URLs.
SOURCES = [('William & Mary', 'https://events.wm.edu/calendar/upcoming/wm'),
           ('Visit Williamsburg', 'https://www.visitwilliamsburg.com/events/')]


def compact(value):
    return re.sub(r'[^a-z0-9]', '', value.lower())


def terms(interests):
    return list(dict.fromkeys(compact(t) for interest in interests for t in [interest, *ALIASES.get(interest.lower(), [])] if compact(t)))


def matches(term, text):
    # Short terms must match a token, not characters inside an unrelated word.
    if len(term) <= 3:
        return term in re.findall(r'[a-z0-9]+', text.lower())
    return term in compact(text)


class RecommendRequest(BaseModel):
    interests: list[str] = Field(min_length=1, max_length=20)
    top_k: int = Field(default=12, ge=1, le=30)
    live_events: bool = False

    @field_validator('interests')
    @classmethod
    def clean_interests(cls, values):
        cleaned = list(dict.fromkeys(value.strip().lower() for value in values if compact(value)))
        if not cleaned or any(len(value) > 60 for value in cleaned):
            raise ValueError('Choose at least one interest; each interest must be at most 60 characters.')
        return cleaned


def club_matches(interests):
    keywords = terms(interests)
    result = []
    for url in CLUBS:
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != 'tribelink.wm.edu':
            continue
        slug = unquote(parsed.path.rsplit('/', 1)[-1])
        hits = [term for term in keywords if matches(term, slug)]
        if hits:
            result.append({'type': 'club', 'title': slug.replace('-', ' ').replace('_', ' ').title(),
                           'url': url, 'score': len(hits), 'reason': 'Matched interests: ' + ', '.join(hits),
                           'source': 'Saved campus directory · September 2025'})
    return sorted(result, key=lambda item: (-item['score'], item['title']))


def parse_events(html, base, interests, source):
    items = {}
    for anchor in BeautifulSoup(html, 'html.parser').find_all('a', href=True):
        url = urljoin(base, anchor['href'])
        parsed = urlparse(url)
        title = anchor.get_text(' ', strip=True)
        is_detail = ('/event/view/' in parsed.path if parsed.netloc == 'events.wm.edu'
                     else bool(re.search(r'/event/[^/]+', parsed.path)))
        if parsed.scheme != 'https' or parsed.netloc != urlparse(base).netloc or not is_detail:
            continue
        hits = [term for term in terms(interests) if re.search(r'\b' + re.escape(term) + r'\b', title, re.IGNORECASE)]
        if len(title) >= 4 and hits:
            items[url] = {'type': 'event', 'title': title, 'url': url, 'score': len(hits),
                          'reason': 'Matching event listing. Verify its date and availability on the source page.', 'source': source}
    return list(items.values())


async def discover_events(interests):
    async with httpx.AsyncClient(timeout=6, follow_redirects=False, headers={'User-Agent': 'Blendin/1.0 campus project'}) as client:
        async def read(source, url):
            try:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 2_000_000:
                            raise ValueError('Listing page too large')
                return parse_events(content.decode('utf-8', errors='replace'), url, interests, source), None
            except (httpx.HTTPError, ValueError):
                return [], f'{source} could not be reached. Campus club matches are still available.'
        results = await asyncio.gather(*(read(*source) for source in SOURCES))
    return [item for items, _ in results for item in items], [warning for _, warning in results if warning]


@app.get('/api/health')
def health():
    return {'status': 'ok', 'clubs': len(CLUBS)}


@app.post('/api/recommend')
async def recommend(req: RecommendRequest):
    clubs = club_matches(req.interests)
    events, warnings = [], []
    if req.live_events:
        try:
            events, warnings = await asyncio.wait_for(discover_events(req.interests), timeout=8)
        except TimeoutError:
            warnings = ['Live search timed out. Showing saved campus club matches.']
        if not events:
            warnings.append('No matching event listings were found. Live calendars may require JavaScript; try the calendar links below.')
    items = sorted(events, key=lambda item: -item['score']) + clubs
    unique = list({item['url']: item for item in items}.values())[:req.top_k]
    return {'items': unique, 'warnings': warnings, 'mode': 'live-and-local' if req.live_events else 'local',
            'directory_note': 'Club links were saved in September 2025; current status is not verified.',
            'calendars': [{'title': source, 'url': url} for source, url in SOURCES]}


# Build once and the Python server can serve the UI without Vite.
if (ROOT / 'client/dist').is_dir():
    app.mount('/', StaticFiles(directory=ROOT / 'client/dist', html=True), name='frontend')
