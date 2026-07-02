from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from recreation_api import get_month_availability, extract_coordinates
from scoring import local_site_score


availability_cache = {}


def month_start(date_obj):
    return date_obj.replace(day=1)


def cached_month_availability(campground_id, month_date):
    key = (campground_id, month_date.strftime("%Y-%m"))

    if key not in availability_cache:
        availability_cache[key] = get_month_availability(campground_id, month_date)

    return availability_cache[key]


def site_available_for_stay(campground_id, campsite_id, check_in, nights):
    for i in range(nights):
        day = check_in + timedelta(days=i)
        month_data = cached_month_availability(campground_id, month_start(day))
        campsite = month_data.get("campsites", {}).get(campsite_id)

        if not campsite:
            return False

        date_key = day.strftime("%Y-%m-%dT00:00:00Z")
        if campsite.get("availabilities", {}).get(date_key) != "Available":
            return False

    return True


def get_available_site_details(campground_id, check_in, nights):
    month_data = cached_month_availability(campground_id, month_start(check_in))
    campsites = month_data.get("campsites", {})

    available = []

    for campsite_id, campsite in campsites.items():
        if not site_available_for_stay(campground_id, campsite_id, check_in, nights):
            continue

        lat, lon = extract_coordinates(campsite)

        site = {
            "campsite_id": campsite_id,
            "site": campsite.get("site", campsite_id),
            "loop": campsite.get("loop", "Unknown"),
            "campsite_type": campsite.get("campsite_type", "Unknown"),
            "type_of_use": campsite.get("type_of_use", "Unknown"),
            "max_num_people": campsite.get("max_num_people", "Unknown"),
            "equipment_length": campsite.get("equipment_length", "Unknown"),
            "latitude": lat,
            "longitude": lon,
        }

        site["local_score"], site["score_reasons"] = local_site_score(site)
        available.append(site)

    return sorted(available, key=lambda s: s["local_score"], reverse=True)


def check_one_date(campground_id, date_obj, nights, friday_saturday_only):
    if friday_saturday_only and date_obj.weekday() not in [4, 5]:
        return None

    sites = get_available_site_details(campground_id, date_obj, nights)

    if not sites:
        return None

    return {
        "date": date_obj.strftime("%Y-%m-%d"),
        "count": len(sites),
        "best_site": sites[0],
    }


def search_possible_dates_parallel(campground_id, start_date, end_date, nights, friday_saturday_only, max_workers=4):
    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_one_date, campground_id, d, nights, friday_saturday_only): d
            for d in dates
        }

        for future in as_completed(futures):
            try:
                item = future.result()
                if item:
                    results.append(item)
            except Exception:
                pass

    return sorted(results, key=lambda x: x["date"])