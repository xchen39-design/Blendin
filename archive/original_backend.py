from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Iterable, Tuple
import pathlib, json, re, asyncio
import httpx
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from dateutil import parser as dateparser

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

app = FastAPI(title="Campus Matcher Backend", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendReq(BaseModel):
    interests: List[str] = Field(default_factory=list)
    top_k: int = 12

SPORT_CHILDREN = [
    "soccer","football","basketball","volleyball","tennis","badminton","table tennis","ping pong",
    "baseball","softball","golf","hockey","lacrosse","rugby","cricket","handball",
    "track","field","cross country","running","run","marathon","triathlon",
    "swim","swimming","diving","rowing","crew","sailing","water polo","surf",
    "cycling","bike","biking","skate","skating","roller","skateboard",
    "ultimate","frisbee","archery","fencing","wrestling","climbing","bouldering","dance","cheer",
    "yoga","fitness","workout","gym","taekwondo","karate","judo","boxing","kickboxing"
]

EXPAND_MAP = {
    "sport": SPORT_CHILDREN,
    "sports": SPORT_CHILDREN,
    "athletic": SPORT_CHILDREN,
    "athletics": SPORT_CHILDREN,
}

ALSO_EVENT_HINTS = ["event","events","calendar","schedule","match","game","tournament","league","fixture","camp","clinic","tryout"]

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def fuzzy_contains(needle: str, hay: str) -> bool:
    if needle in hay:
        return True
    return SequenceMatcher(None, needle, hay).ratio() >= 0.80

def expand_interests(words: Iterable[str]) -> List[str]:
    out: List[str] = []
    for w in words:
        w_norm = normalize(w)
        if not w_norm:
            continue
        out.append(w_norm)
        if w_norm in EXPAND_MAP:
            out.extend(EXPAND_MAP[w_norm])
        if w_norm.endswith("s"):
            out.append(w_norm[:-1])
        else:
            out.append(w_norm + "s")
    seen = set(); uniq=[]
    for w in out:
        if w and w not in seen:
            uniq.append(w); seen.add(w)
    return uniq

def load_club_links() -> List[str]:
    json_path = DATA_DIR / "club_links.json"
    txt_path = DATA_DIR / "club_links.txt"
    links: List[str] = []
    if json_path.exists():
        try:
            links = json.loads(json_path.read_text())
        except Exception:
            links = []
    if not links and txt_path.exists():
        for line in txt_path.read_text().splitlines():
            u = line.strip()
            if u.startswith("http"):
                links.append(u)
    return links

def club_name_from_url(url: str) -> str:
    m = re.search(r'/organization/([^/?#]+)', url)
    return m.group(1) if m else url.split("/")[-1]

async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, timeout=10)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return ""
    return ""

def extract_date_near(node) -> Tuple[str, float]:
    text = " ".join([node.get_text(" ", strip=True) or ""])
    parent = node.find_parent()
    if parent:
        text += " " + (parent.get_text(" ", strip=True) or "")
    text = re.sub(r"\s+", " ", text)
    try:
        dt = dateparser.parse(text, fuzzy=True)
        if dt:
            return (dt.strftime("%Y-%m-%d"), 0.08)
    except Exception:
        pass
    return ("", 0.0)

async def find_event_links_from_club(client: httpx.AsyncClient, club_url: str, kwds: List[str]) -> List[Dict[str, Any]]:
    try:
        html = await fetch_html(client, club_url)
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        out: List[Dict[str, Any]] = []
        for a in soup.find_all("a"):
            text = (a.get_text(" ", strip=True) or "").lower()
            href = (a.get("href") or "").lower()
            tnorm = normalize(text); hnorm = normalize(href)
            hit_eventy = any(h in href or h in text for h in ALSO_EVENT_HINTS)
            hit_kw = any(fuzzy_contains(normalize(k), tnorm) or fuzzy_contains(normalize(k), hnorm) for k in kwds)
            if hit_eventy or hit_kw:
                url = a.get("href") or club_url
                if url.startswith("/"):
                    from urllib.parse import urljoin
                    url = urljoin(club_url, url)
                title = a.get_text(" ", strip=True) or "Event"
                score = 0.9 if (hit_eventy and hit_kw) else (0.8 if hit_eventy else 0.7)
                d, bonus = extract_date_near(a)
                if d: title = f"{title} · {d}"; score += bonus
                out.append({"type":"event","title":title,"url":url,"score":score,"reason":"club page"})
        dedup: Dict[str, Dict[str, Any]] = {}
        for it in out:
            u = it["url"]
            if u not in dedup or it["score"] > dedup[u]["score"]:
                dedup[u] = it
        return list(dedup.values())
    except Exception:
        return []

async def scrape_generic_events(client: httpx.AsyncClient, base: str, paths: List[str], kwds: List[str], source: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    tried = []
    for p in [""] + paths:
        url = base + p
        if url in tried: continue
        tried.append(url)
        html = await fetch_html(client, url)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a"):
            text = (a.get_text(" ", strip=True) or "")
            href = a.get("href") or ""
            tnorm = normalize(text); hnorm = normalize(href)
            hit_eventy = any(h in href.lower() or h in text.lower() for h in ALSO_EVENT_HINTS)
            hit_kw = any(fuzzy_contains(normalize(k), tnorm) or fuzzy_contains(normalize(k), hnorm) for k in kwds)
            if hit_kw or hit_eventy:
                url2 = href
                if url2.startswith("/"):
                    from urllib.parse import urljoin
                    url2 = urljoin(base, url2)
                title = text if text else "Event"
                score = 0.95 if (hit_kw and hit_eventy) else (0.85 if hit_eventy else 0.75)
                d, bonus = extract_date_near(a)
                if d: title = f"{title} · {d}"; score += bonus
                out.append({"type":"event","title":title,"url":url2,"score":score,"reason":source})
    dedup: Dict[str, Dict[str, Any]] = {}
    for it in out:
        u = it["url"]
        if u not in dedup or it["score"] > dedup[u]["score"]:
            dedup[u] = it
    return list(dedup.values())

async def scrape_wm_dot_edu(client: httpx.AsyncClient, kwds: List[str]) -> List[Dict[str, Any]]:
    base = "https://events.wm.edu"
    q = "|".join(re.escape(k) for k in kwds[:6])  # 关键词多时别太长
    paths = [
        "/",
        "/calendar/",
        f"/?s={kwds[0]}",
        f"/search/?q={kwds[0]}",
        f"/?q={kwds[0]}",
        f"/search/{kwds[0]}",
    ]
    items = await scrape_generic_events(client, base, paths, kwds, "wm.edu")
    # 过滤明显与体育不相关的（若原始兴趣含 sport 类）
    if any(k in ("sport","sports") for k in kwds):
        keep = []
        for it in items:
            nm = normalize(it["title"])
            if any(w in nm for w in ["sport","soccer","football","basketball","tennis","volleyball","track","run","swim","golf","hockey","lacrosse","rugby","frisbee","ultimate","baseball","softball"]):
                keep.append(it)
        if keep: items = keep
    return items

async def scrape_visit_williamsburg(client: httpx.AsyncClient, kwds: List[str]) -> List[Dict[str, Any]]:
    base = "https://www.visitwilliamsburg.com/events/"
    paths = [
        "",  # 列表页
        f"?s={kwds[0]}",
        f"?q={kwds[0]}",
        f"search/{kwds[0]}",
    ]
    return await scrape_generic_events(client, base, paths, kwds, "visitwilliamsburg")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/debug")
def debug():
    links = load_club_links()
    return {"clubs": len(links)}

@app.post("/recommend")
async def recommend(req: RecommendReq):
    raw = [w for w in req.interests if w]
    expanded = expand_interests(raw)
    expanded_norm = [normalize(w) for w in expanded if w]

    links = load_club_links()
    matched_clubs: List[str] = []
    for u in links:
        name = club_name_from_url(u)
        hay = normalize(name) + " " + normalize(u)
        if any(fuzzy_contains(k, hay) for k in expanded_norm):
            matched_clubs.append(u)
    if not matched_clubs and any(k in ("sport","sports") for k in expanded_norm):
        matched_clubs = links[:12]

    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        tasks.append(scrape_wm_dot_edu(client, expanded_norm))
        tasks.append(scrape_visit_williamsburg(client, expanded_norm))
        club_tasks = [find_event_links_from_club(client, u, expanded_norm) for u in matched_clubs[:12]]
        tasks.extend(club_tasks)
        results = await asyncio.gather(*tasks, return_exceptions=True)

    agg: List[Dict[str, Any]] = []
    # 0: wm.edu, 1: visitwilliamsburg, 2.. club pages
    for r in results:
        if isinstance(r, list):
            agg.extend(r)

    if not agg:
        for u in matched_clubs[:12]:
            agg.append({
                "type":"club","title":club_name_from_url(u),"url":u,
                "score":0.6,"reason":"matched club; no external event"
            })

    dedup: Dict[str, Dict[str, Any]] = {}
    for it in agg:
        u = it["url"]
        if u not in dedup or it.get("score",0) > dedup[u].get("score",0):
            dedup[u] = it
    items = list(dedup.values())
    items = sorted(items, key=lambda x: x.get("score",0), reverse=True)
    if req.top_k and req.top_k>0:
        items = items[:req.top_k]

    if not items:
        items = [{
            "type":"suggestion",
            "title":"Try Sports & Recreation category",
            "url":"https://tribelink.wm.edu/organizations?categories=sports",
            "score":0.2,
            "reason":"no club/event matched"
        }]
    return {"items": items}





