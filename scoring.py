from utils import safe_int


def local_site_score(site):
    score = 0
    reasons = []

    max_people = safe_int(site.get("max_num_people"))
    equipment_length = safe_int(site.get("equipment_length"))
    site_type = str(site.get("campsite_type", "")).lower()
    loop = str(site.get("loop", "")).lower()

    if max_people:
        score += max_people * 2
        reasons.append(f"Capacity: up to {max_people} people")

    if equipment_length:
        score += equipment_length / 4
        reasons.append(f"Equipment length: {equipment_length}")

    if "standard" in site_type:
        score += 15
        reasons.append("Standard campsite type")
    if "tent" in site_type:
        score += 10
        reasons.append("Tent-compatible")
    if "rv" in site_type:
        score += 8
        reasons.append("RV-compatible")
    if "group" in site_type:
        score += 5
        reasons.append("Group campsite")

    if loop and loop != "unknown":
        score += 8
        reasons.append(f"Loop listed: {site.get('loop')}")

    if not reasons:
        reasons.append("Limited site details available")

    return min(100, round(score, 1)), reasons


def combine_site_and_review_score(site_score, review_score):
    return round(min(100, site_score) * 0.55 + review_score * 0.45, 1)


def combined_site_score(site, review_summary):
    return combine_site_and_review_score(
        site.get("local_score", 0),
        review_summary.get("review_score", 70)
    )


def stars_from_score(score):
    stars = max(1, min(5, round(score / 20)))
    return "★" * stars + "☆" * (5 - stars)


def star_count_from_score(score):
    return max(1, min(5, round(score / 20)))


def color_from_score(score):
    stars = star_count_from_score(score)

    if stars >= 4:
        return "#2e7d32"   # green
    if stars == 3:
        return "#f9a825"   # yellow
    return "#c62828"       # red