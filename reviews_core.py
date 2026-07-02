import re
import time
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}
REVIEW_TIME_LIMIT_SECONDS = 5
review_cache = {}

POSITIVE_WORDS = [
    "beautiful", "quiet", "clean", "spacious", "scenic", "great", "excellent",
    "friendly", "private", "peaceful", "nice", "amazing", "family", "shade",
    "lake", "river", "hiking", "views", "well maintained", "large", "good",
    "wonderful", "favorite", "recommend", "loved"
]

NEGATIVE_WORDS = [
    "noisy", "crowded", "dirty", "small", "tight", "bugs", "mosquito",
    "dusty", "rough", "poor", "bad", "limited", "traffic", "generator",
    "close together", "no privacy", "steep", "problem", "broken"
]

SOURCE_DOMAINS = [
    "recreation.gov", "campendium.com", "thedyrt.com", "tripadvisor.com",
    "yelp.com", "reddit.com", "rvlife.com", "campgroundreviews.com",
]


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def time_left(start_time):
    return REVIEW_TIME_LIMIT_SECONDS - (time.time() - start_time)


def safe_get(url, start_time):
    remaining = time_left(start_time)

    if remaining <= 0:
        raise TimeoutError("Review search time limit reached.")

    r = requests.get(url, headers=HEADERS, timeout=max(1, min(remaining, 2.0)))
    r.raise_for_status()
    return r


def extract_duckduckgo_url(href):
    if not href:
        return None

    if href.startswith("/l/?"):
        parsed = urlparse(href)
        query = parse_qs(parsed.query)

        if "uddg" in query:
            return unquote(query["uddg"][0])

    if href.startswith("http"):
        return href

    return None


def fetch_page_text(url, start_time):
    try:
        r = safe_get(url, start_time)
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    return clean_text(soup.get_text(" "))[:8000]


def get_search_result_links(query, start_time, max_links=6):
    try:
        r = safe_get(f"https://duckduckgo.com/html/?q={quote_plus(query)}", start_time)
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = extract_duckduckgo_url(a.get("href"))

        if not href:
            continue

        lower = href.lower()

        if any(blocked in lower for blocked in ["facebook", "instagram", "login", "signin"]):
            continue

        if any(domain in lower for domain in SOURCE_DOMAINS):
            if href not in links:
                links.append(href)

        if len(links) >= max_links:
            break

    return links


def collect_review_text(campground):
    start_time = time.time()
    name = campground["name"]
    pieces = []

    official_text = fetch_page_text(campground["url"], start_time)
    if official_text:
        pieces.append(official_text)

    queries = [
        f'"{name}" campground reviews',
        f'"{name}" camping reviews',
        f'"{name}" Reddit campground',
        f'"{name}" The Dyrt',
        f'"{name}" Campendium',
    ]

    visited = set()

    for query in queries:
        if time_left(start_time) <= 0:
            break

        for link in get_search_result_links(query, start_time):
            if time_left(start_time) <= 0:
                break

            if link in visited:
                continue

            visited.add(link)
            text = fetch_page_text(link, start_time)

            if text and any(word in text.lower() for word in ["campground", "camping", "campsite"]):
                pieces.append(text[:5000])

    return "\n".join(pieces)


def count_words(text, words):
    lower = text.lower()
    return sum(lower.count(word) for word in words)


def extract_comment_summary(text):
    lower = text.lower()

    positives = []
    negatives = []

    pos_patterns = [
        ("Scenic setting", ["beautiful", "scenic", "views", "view"]),
        ("Quiet atmosphere", ["quiet", "peaceful"]),
        ("Family friendly", ["family", "kids", "children"]),
        ("Clean / maintained", ["clean", "well maintained"]),
        ("Shade / forest", ["shade", "forested", "trees"]),
        ("Good hiking or water access", ["hiking", "trail", "lake", "river"]),
    ]

    neg_patterns = [
        ("Crowded / busy", ["crowded", "busy"]),
        ("Sites close together", ["close together", "no privacy"]),
        ("Noise", ["noisy", "generator", "traffic"]),
        ("Bugs / mosquitoes", ["bugs", "mosquito"]),
        ("Small / tight sites", ["small", "tight"]),
        ("Limited service", ["limited", "no cell", "cell signal"]),
    ]

    for label, keys in pos_patterns:
        if any(k in lower for k in keys):
            positives.append(label)

    for label, keys in neg_patterns:
        if any(k in lower for k in keys):
            negatives.append(label)

    return positives[:4], negatives[:4]


def score_reviews_from_text(text):
    if not text or len(text) < 300:
        return {
            "review_score": 70,
            "confidence": "none",
            "positives": [],
            "negatives": [],
            "important": ["Review data limited"],
        }

    positive_count = count_words(text, POSITIVE_WORDS)
    negative_count = count_words(text, NEGATIVE_WORDS)

    raw = 70 + positive_count * 2.5 - negative_count * 3.5
    score = int(max(30, min(98, raw)))

    positives, negatives = extract_comment_summary(text)

    confidence = "low"
    if len(text) > 5000:
        confidence = "medium"
    if len(text) > 15000:
        confidence = "high"

    return {
        "review_score": score,
        "confidence": confidence,
        "positives": positives,
        "negatives": negatives,
        "important": [f"Review confidence: {confidence}"],
    }


def get_campground_review_summary(campground):
    campground_id = campground["id"]

    if campground_id in review_cache:
        return review_cache[campground_id]

    result = score_reviews_from_text(collect_review_text(campground))
    review_cache[campground_id] = result
    return result