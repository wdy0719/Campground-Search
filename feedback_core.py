import json
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = Path("feedback_data.json")


def load_feedback():
    if not FEEDBACK_FILE.exists():
        return {}

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_feedback(data):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_feedback(campground, vote):
    data = load_feedback()
    campground_id = campground["id"]

    if campground_id not in data:
        data[campground_id] = {
            "name": campground["name"],
            "thumbs_up": 0,
            "thumbs_down": 0,
            "history": []
        }

    if vote == "up":
        data[campground_id]["thumbs_up"] += 1
    elif vote == "down":
        data[campground_id]["thumbs_down"] += 1

    data[campground_id]["history"].append({
        "vote": vote,
        "time": datetime.now().isoformat()
    })

    save_feedback(data)


def get_feedback_summary(campground):
    data = load_feedback()
    campground_id = campground["id"]

    if campground_id not in data:
        return {
            "thumbs_up": 0,
            "thumbs_down": 0,
            "total": 0,
            "percent_positive": None
        }

    up = data[campground_id].get("thumbs_up", 0)
    down = data[campground_id].get("thumbs_down", 0)
    total = up + down

    return {
        "thumbs_up": up,
        "thumbs_down": down,
        "total": total,
        "percent_positive": round(up / total * 100, 1) if total else None
    }