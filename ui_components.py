import streamlit as st
from scoring import combined_site_score, stars_from_score, color_from_score


def inject_css():
    st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 17px !important; }
    .big-title { font-size: 34px; font-weight: 800; }
    .section-title { font-size: 24px; font-weight: 700; margin-top: 1rem; }
    .card {
        border-radius: 18px;
        padding: 16px;
        margin: 10px 0;
        border: 2px solid #ddd;
        background-color: #fafafa;
    }
    .important { background-color: #fff3cd; border-left: 10px solid #f9a825; padding: 10px; border-radius: 10px; }
    .good { background-color: #d8f3dc; border-left: 10px solid #2e7d32; padding: 10px; border-radius: 10px; }
    .bad { background-color: #fde2e2; border-left: 10px solid #c62828; padding: 10px; border-radius: 10px; }
    .stars { font-size: 26px; font-weight: 800; }
    .reserve-info { font-size: 18px; line-height: 1.5; }
    div.stButton > button { font-size: 18px !important; border-radius: 14px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)


def title():
    st.markdown('<div class="big-title">🏕️ Campsite Finder</div>', unsafe_allow_html=True)
    st.write("Simplified reservation-focused view.")


def section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def color_block(title_text, items, css_class):
    if not items:
        return
    html = f"<div class='{css_class}'><b>{title_text}</b><br>"
    for item in items:
        html += f"• {item}<br>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def campground_summary(campground, review):
    score = review.get("review_score", 70)
    stars = stars_from_score(score)
    color = color_from_score(score)

    st.markdown(f"""
    <div class="card">
        <div style="font-size:28px;font-weight:800;">{campground["name"]}</div>
        <div class="stars" style="color:{color};">{stars}</div>
    </div>
    """, unsafe_allow_html=True)

    color_block("Important Information", review.get("important", []), "important")
    color_block("Strengths", review.get("positives", []), "good")
    color_block("Potential Concerns", review.get("negatives", []), "bad")


def official_map_button(campground):
    st.link_button("Open official Recreation.gov page / map", campground["url"])


def reservation_card(site, campground, check_in, nights, review):
    combined = combined_site_score(site, review)
    stars = stars_from_score(combined)
    color = color_from_score(combined)
    reasons = "; ".join(site.get("score_reasons", ["Limited site details available"]))

    st.markdown(f"""
    <div class="card">
        <div style="font-size:28px;font-weight:800;">Site {site["site"]}</div>
        <div class="stars" style="color:{color};">{stars}</div>
        <div class="reserve-info">
            <b>Campground:</b> {campground["name"]}<br>
            <b>Check-in:</b> {check_in}<br>
            <b>Nights:</b> {nights}<br>
            <b>Loop:</b> {site["loop"]}<br>
            <b>Type:</b> {site["campsite_type"]}<br>
            <b>Max people:</b> {site["max_num_people"]}<br>
            <b>Equipment length:</b> {site["equipment_length"]}<br>
            <b>Why this rating:</b> {reasons}<br>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.link_button("Reserve / View on Recreation.gov", campground["url"])


def date_card(date_item, campground, nights, review, unique_suffix=""):
    best_site = date_item.get("best_site", {})
    best_label = best_site.get("site", "?")

    if best_site:
        date_score = combined_site_score(best_site, review)
    else:
        date_score = review.get("review_score", 70)

    stars = stars_from_score(date_score)
    color = color_from_score(date_score)

    st.markdown(f"""
    <div class="card">
        <div style="font-size:26px;font-weight:800;">{date_item["date"]}</div>
        <div class="stars" style="color:{color};">{stars}</div>
        <div class="reserve-info">
            <b>Open sites:</b> {date_item["count"]}<br>
            <b>Best available site:</b> {best_label}<br>
            <b>Date rating based on:</b> best available campsite + public campground review data
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        f"Show sites for {date_item['date']}",
        key=f"date-{campground['id']}-{date_item['date']}-{unique_suffix}"
    ):
        st.session_state["selected_date"] = date_item["date"]
        st.session_state["selected_campground"] = campground
        st.session_state["selected_review"] = review
        st.session_state["page"] = "sites"
        st.rerun()