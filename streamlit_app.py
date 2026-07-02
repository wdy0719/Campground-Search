from datetime import datetime
import streamlit as st

from recreation_api import search_campgrounds
from campsite_core import get_available_site_details, search_possible_dates_parallel
from reviews_core import get_campground_review_summary
from scoring import combined_site_score
from utils import to_datetime, APP_VERSION
from ui_components import (
    inject_css,
    title,
    section_title,
    campground_summary,
    reservation_card,
    date_card,
    official_map_button,
)


st.set_page_config(page_title="Campsite Finder", page_icon="🏕️", layout="wide")
inject_css()


@st.cache_data(show_spinner=False)
def cached_search_campgrounds(query):
    return search_campgrounds(query)


@st.cache_data(show_spinner=False)
def cached_review(campground):
    return get_campground_review_summary(campground)


@st.cache_data(show_spinner=False)
def cached_sites(campground_id, check_in, nights):
    return get_available_site_details(campground_id, check_in, nights)


@st.cache_data(show_spinner=False)
def cached_flexible_dates(campground_id, start_date, end_date, nights, friday_saturday_only):
    return search_possible_dates_parallel(
        campground_id,
        start_date,
        end_date,
        nights,
        friday_saturday_only,
        max_workers=4
    )


if "page" not in st.session_state:
    st.session_state["page"] = "dates"


title()
st.caption(APP_VERSION)

with st.sidebar:
    st.header("Search")

    park_query = st.text_input("Park or campground", value="")
    start_date = st.date_input("Start date")
    end_date = st.date_input("End date")
    nights = st.number_input("Nights", min_value=1, max_value=14, value=2)

    flexible = st.checkbox("Flexible date range search", value=True)
    friday_saturday_only = st.checkbox("Friday/Saturday check-ins only", value=False)

    if st.button("Find campgrounds"):
        if park_query.strip():
            with st.spinner("Finding campgrounds..."):
                st.session_state["campgrounds"] = cached_search_campgrounds(park_query.strip())
                st.session_state["availability_ready"] = False
                st.session_state["page"] = "dates"
                st.session_state.pop("selected_date", None)


if "campgrounds" not in st.session_state:
    st.info("Enter a park or campground name to begin.")
    st.stop()

campgrounds = st.session_state["campgrounds"]

if not campgrounds:
    st.warning("No campgrounds found.")
    st.stop()

campground_names = [f"{c['name']} | ID {c['id']}" for c in campgrounds]

selected_names = st.multiselect(
    "Select campground(s)",
    campground_names,
    default=[campground_names[0]]
)

selected_campgrounds = [
    campgrounds[campground_names.index(name)]
    for name in selected_names
]

if not selected_campgrounds:
    st.warning("Select at least one campground.")
    st.stop()

if st.button("Search Availability"):
    st.session_state["availability_ready"] = True
    st.session_state["page"] = "dates"
    st.session_state.pop("selected_date", None)

if not st.session_state.get("availability_ready"):
    st.stop()

start_dt = to_datetime(start_date)
end_dt = to_datetime(end_date)

if end_dt < start_dt:
    st.error("End date must be after start date.")
    st.stop()


tab_dates, tab_sites = st.tabs(["Available Dates", "Campsites"])


with tab_dates:
    if st.session_state["page"] == "sites":
        st.info("You selected a date. Open the Campsites tab to view available sites.")

    for campground in selected_campgrounds:
        with st.spinner(f"Checking {campground['name']}..."):
            review = cached_review(campground)

        campground_summary(campground, review)
        official_map_button(campground)

        if flexible:
            with st.spinner("Searching available dates..."):
                dates = cached_flexible_dates(
                    campground["id"],
                    start_dt,
                    end_dt,
                    int(nights),
                    friday_saturday_only
                )

            if not dates:
                st.warning("No available dates found.")
                continue

            section_title("Available Dates")
            cols = st.columns(3)

            for index, item in enumerate(dates):
                with cols[index % 3]:
                    date_card(
                        item,
                        campground,
                        int(nights),
                        review,
                        unique_suffix=f"{campground['id']}-{index}"
                    )

        else:
            with st.spinner("Searching available sites..."):
                sites = cached_sites(campground["id"], start_dt, int(nights))

            if not sites:
                st.warning("No available sites found.")
                continue

            section_title("Available Sites")

            sorted_sites = sorted(
                sites,
                key=lambda s: combined_site_score(s, review),
                reverse=True
            )

            for site in sorted_sites[:6]:
                reservation_card(site, campground, start_date, int(nights), review)


with tab_sites:
    if "selected_date" not in st.session_state:
        st.info("Choose a date from the Available Dates tab first.")
    else:
        selected_date = st.session_state["selected_date"]
        selected_campground = st.session_state["selected_campground"]
        selected_review = st.session_state["selected_review"]

        section_title(f"Sites for {selected_date}")
        official_map_button(selected_campground)

        if st.button("← Back to Available Dates"):
            st.session_state["page"] = "dates"
            st.rerun()

        selected_dt = datetime.strptime(selected_date, "%Y-%m-%d")

        with st.spinner("Loading sites..."):
            sites = cached_sites(
                selected_campground["id"],
                selected_dt,
                int(nights)
            )

        sorted_sites = sorted(
            sites,
            key=lambda s: combined_site_score(s, selected_review),
            reverse=True
        )

        for site in sorted_sites[:6]:
            reservation_card(
                site,
                selected_campground,
                selected_date,
                int(nights),
                selected_review
            )