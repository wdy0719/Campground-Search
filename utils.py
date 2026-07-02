from datetime import datetime, time


APP_VERSION = "v1.0-streamlit-modular"


def to_datetime(date_value):
    return datetime.combine(date_value, time.min)


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default