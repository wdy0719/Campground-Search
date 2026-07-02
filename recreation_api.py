import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}


def extract_coordinates(item):
    if not isinstance(item, dict):
        return None, None

    lat_keys = ["latitude", "Latitude", "lat", "FacilityLatitude", "RecAreaLatitude"]
    lon_keys = ["longitude", "Longitude", "lon", "lng", "FacilityLongitude", "RecAreaLongitude"]

    lat = next((item.get(k) for k in lat_keys if item.get(k) not in [None, ""]), None)
    lon = next((item.get(k) for k in lon_keys if item.get(k) not in [None, ""]), None)

    try:
        return float(lat), float(lon)
    except Exception:
        return None, None


def search_campgrounds(query):
    url = "https://www.recreation.gov/api/search"
    params = {"q": query, "inventory_type": "camping", "size": 50}

    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()

    matches = []

    for item in r.json().get("results", []):
        name = item.get("name") or item.get("title")
        entity_id = item.get("entity_id") or item.get("id")
        entity_type = item.get("entity_type", "")

        if not name or not entity_id:
            continue

        if "campground" not in name.lower() and entity_type != "campground":
            continue

        lat, lon = extract_coordinates(item)

        matches.append({
            "name": name,
            "id": str(entity_id),
            "latitude": lat,
            "longitude": lon,
            "url": f"https://www.recreation.gov/camping/campgrounds/{entity_id}",
        })

    return matches


def get_month_availability(campground_id, month_date):
    url = f"https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"
    params = {"start_date": month_date.strftime("%Y-%m-%dT00:00:00.000Z")}

    r = requests.get(url, params=params, headers=HEADERS, timeout=20)

    if r.status_code == 404:
        raise ValueError("Availability could not be found for this campground.")

    r.raise_for_status()
    return r.json()