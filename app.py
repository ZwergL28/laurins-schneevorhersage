import base64
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from snow_checker import load_forecast, to_table, will_it_snow_between


# --------------------------------------------------
# PAGE CONFIG (NUR EINMAL!)
# --------------------------------------------------
st.set_page_config(
    page_title="Laurins Schneevorhersage",
    page_icon="❄️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# MOBILE & UI CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    button { min-height: 48px; }

    h1, h2, h3 { text-align: center; }

    @media (max-width: 600px) {
        iframe { height: 70vh !important; }
    }

    div.stButton > button {
        display: block;
        margin: 2rem auto;
        background-color: #1f77ff;
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.6rem 2.2rem;
        border-radius: 10px;
        border: none;
    }

    div.stButton > button:hover {
        background-color: #155edb;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# DATA
# --------------------------------------------------
PLACES = {
    "Bettingen (BS)": (47.57, 7.66),
    "Basel SBB": (47.547, 7.589),
    "Davos": (46.802, 9.835),
    "Zermatt": (46.020, 7.749),
    "Zürich": (47.376, 8.541),
    "Flims/Laax": (46.838, 9.286),
    "Grindelwald": (46.624, 8.035),
    "Hasliberg": (46.757, 8.151),
    "Arosa": (46.777, 9.678),
    "St. Gallen": (47.424, 9.375),
    "Klosters": (46.9, 9.9),
    "Churwalden": (46.78, 9.54),
    "St. Moritz": (46.488, 9.835),
    "Innsbruck": (47.268, 11.393),
}


# --------------------------------------------------
# BACKGROUND
# --------------------------------------------------
def set_background(image_file: str) -> None:
    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .block-container {{
            background: rgba(255,255,255,0.85);
            border-radius: 16px;
            padding: 1.2rem;
            max-width: 900px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# STATE DEFAULTS
# --------------------------------------------------
def ensure_state_defaults() -> None:
    st.session_state.setdefault("lat", 47.57)
    st.session_state.setdefault("lon", 7.66)
    st.session_state.setdefault("place_name", "Bettingen (BS)")
    st.session_state.setdefault("map_fullscreen", False)
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("scroll_to_result", False)


def on_place_change() -> None:
    lat, lon = PLACES[st.session_state.place_name]
    st.session_state.lat = lat
    st.session_state.lon = lon


# --------------------------------------------------
# MAP
# --------------------------------------------------
def draw_clickable_map() -> None:
    previous = st.session_state.get("map")
    if previous and previous.get("last_clicked"):
        st.session_state.lat = previous["last_clicked"]["lat"]
        st.session_state.lon = previous["last_clicked"]["lng"]

    height = 850 if st.session_state.map_fullscreen else 450

    m = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=11,
        control_scale=True,
    )

    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Gewählter Ort",
    ).add_to(m)

    st_folium(m, height=height, key="map")


# --------------------------------------------------
# UI START
# --------------------------------------------------
set_background("davos.jpg")
ensure_state_defaults()

st.title("❄️ Schneit es noch vor Weihnachten?")
st.write("Wir prüfen, ob es zwischen dem gewählten Zeitraum irgendwo schneit.")

start_date = st.date_input("Startdatum", value=pd.to_datetime("2025-12-16").date())
end_date = st.date_input("Enddatum", value=pd.to_datetime("2025-12-25").date())

st.selectbox(
    "Ort auswählen",
    list(PLACES.keys()),
    key="place_name",
    on_change=on_place_change,
)

st.subheader("Ort auf der Karte anklicken")
draw_clickable_map()

st.checkbox("Karte gross anzeigen", key="map_fullscreen")


# --------------------------------------------------
# BUTTON (EVENT)
# --------------------------------------------------
if st.button("❄️ Schneevorhersage berechnen"):
    with st.spinner("Berechne Schneevorhersage…"):
        data = load_forecast(st.session_state.lat, st.session_state.lon)
        df = to_table(data)

        will_snow, total_snow_cm, snow_hours, window = will_it_snow_between(
            df, str(start_date), str(end_date)
        )

    st.session_state.result = {
        "will_snow": will_snow,
        "total_snow_cm": total_snow_cm,
        "snow_hours": snow_hours,
        "window": window,
    }

    st.session_state.scroll_to_result = True
    st.rerun()


# --------------------------------------------------
# RESULT + AUTO SCROLL (ROBUST MOBILE)
# --------------------------------------------------
if st.session_state.result is not None:

    st.markdown("<div id='result'></div>", unsafe_allow_html=True)

    st.markdown("## ❄️ Ergebnis der Schneevorhersage")
    result = st.session_state.result

    if result["will_snow"]:
        st.success(
            f"❄️ Ja – es wird schneien. Erwartete Menge: {result['total_snow_cm']:.2f} cm"
        )
        st.dataframe(
            result["snow_hours"][["time", "snowfall_cm", "temp_c"]],
            use_container_width=True
        )
    else:
        st.warning("🌧️ Nein – laut Vorhersage kein Schneefall.")

    st.caption("Hinweis: Vorhersagen werden unsicherer, je weiter sie in der Zukunft liegen.")
    st.dataframe(
        result["window"][["time", "snowfall_cm", "temp_c", "precip_mm"]],
        use_container_width=True
    )

    if st.session_state.scroll_to_result:
        st.markdown(
            """
            <script>
            setTimeout(function() {
                const el = document.getElementById("result");
                if (el) {
                    el.scrollIntoView({behavior: "smooth"});
                }
            }, 300);
            </script>
            """,
            unsafe_allow_html=True
        )
        st.session_state.scroll_to_result = False
